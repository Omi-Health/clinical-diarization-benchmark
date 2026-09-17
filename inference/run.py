"""Run a local checkpoint on the frozen audio; configuration is supplied separately."""
import argparse
from contextlib import nullcontext
import hashlib
import json
from pathlib import Path
import platform
import tempfile
import time
import wave

from .processing import normalize_max_speakers, parse_native, probability_segments, stitch_windows

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1048576), b''):
            h.update(chunk)
    return h.hexdigest()


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, allow_nan=False) + '\n')


def windowed_inference(model, audio, window_s, overlap_s):
    """Historical WAV slicing, native millisecond parsing and overlap stitching."""
    if not 0 <= overlap_s < window_s:
        raise ValueError('Require 0 <= overlap_s < window_s')
    with wave.open(str(audio)) as f:
        sr, ch, width = f.getframerate(), f.getnchannels(), f.getsampwidth()
        pcm = f.readframes(f.getnframes())
    bps = sr * ch * width
    window_b, step_b = int(window_s * bps), int((window_s-overlap_s) * bps)
    frame = ch * width
    window_b -= window_b % frame
    step_b -= step_b % frame
    if step_b <= 0:
        raise ValueError('Window step must contain at least one audio frame')
    windows, starts = [], []
    with tempfile.TemporaryDirectory() as directory:
        path = Path(directory) / 'window.wav'
        for start in range(0, len(pcm), step_b):
            end = min(start + window_b, len(pcm))
            with wave.open(str(path), 'wb') as f:
                f.setparams((ch, width, sr, 0, 'NONE', 'not compressed'))
                f.writeframes(pcm[start:end])
            annotations = model.diarize(audio=str(path), batch_size=1, num_workers=0, verbose=False)
            windows.append(parse_native(annotations, legacy_ms=True))
            starts.append(int(start/bps*1000))
            if end >= len(pcm):
                break
    if len(windows) == 1:
        return windows[0]
    return stitch_windows(windows, starts, int(overlap_s*1000))


def configure(model, config):
    expected = config.get('streaming_mode')
    if expected is not None and bool(model.streaming_mode) != expected:
        raise ValueError('Checkpoint streaming mode does not match the configuration')
    geometry = config.get('geometry', {})
    if geometry:
        modules = model.sortformer_modules
        for key, value in geometry.items():
            if not hasattr(modules, key) or type(value) is not int or value < 0:
                raise ValueError('Invalid geometry attribute or value')
            setattr(modules, key, value)
        checker = getattr(model, '_check_streaming_parameters', None)
        if checker is None:
            checker = getattr(modules, '_check_streaming_parameters', None)
        if checker is None:
            raise RuntimeError('Runtime has no geometry validator')
        checker()
        return {key: int(getattr(modules, key)) for key in geometry}
    return {}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--checkpoint', type=Path, required=True)
    parser.add_argument('--audio-dir', type=Path, default=ROOT/'data/raw_audio')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    mode = config['mode']
    if mode not in {'legacy_windowed', 'native', 'probabilities'}:
        raise ValueError('Unknown inference mode')
    precision = config['precision']
    if precision not in {'fp32', 'bf16'}:
        raise ValueError('precision must be fp32 or bf16')
    if config.get('fold_to') not in {None, 2}:
        raise ValueError('Only historical fold-to-two is supported')
    # Private configurations and generated outputs belong outside tracked source/data.
    output = args.output.resolve()
    if output.is_relative_to(ROOT) and not output.is_relative_to(ROOT/'private'):
        raise ValueError('Use private/ or an output directory outside this repository')
    output.mkdir(parents=True, exist_ok=True)
    if any(output.iterdir()):
        raise ValueError('Output directory must be empty; preserve earlier runs')
    checkpoint_hash = sha(args.checkpoint)
    expected_hash = config.get('checkpoint_sha256')
    if expected_hash and checkpoint_hash != expected_hash:
        raise ValueError('Checkpoint hash mismatch')
    cases = json.loads((ROOT/'data/manifest.json').read_text())['recordings']
    for case in cases:
        audio = args.audio_dir / (case['case']+'_conversation.wav')
        if sha(audio) != case['audio_sha256']:
            raise ValueError(f"Audio hash mismatch: {case['case']}")
        with wave.open(str(audio)) as f:
            if (f.getframerate(), f.getnchannels(), f.getsampwidth()) != (16000, 1, 2):
                raise ValueError('Expected 16 kHz mono PCM16')
    import torch
    import nemo
    from nemo.collections.asr.models import SortformerEncLabelModel
    if not torch.cuda.is_available():
        raise RuntimeError('CUDA is required for inference')
    if precision == 'bf16' and not torch.cuda.is_bf16_supported():
        raise RuntimeError('BF16 support required')
    if config.get('matmul_precision'):
        torch.set_float32_matmul_precision(config['matmul_precision'])
    model = SortformerEncLabelModel.restore_from(str(args.checkpoint), map_location='cpu', strict=config['strict'])
    dtype = torch.bfloat16 if precision == 'bf16' else torch.float32
    model = model.to(device='cuda', dtype=dtype).eval()
    geometry = configure(model, config)
    receipt = dict(configuration=config, effective_geometry=geometry,
                   checkpoint_sha256=checkpoint_hash, runner_sha256=sha(__file__),
                   processing_sha256=sha(Path(__file__).with_name('processing.py')),
                   manifest_sha256=sha(ROOT/'data/manifest.json'),
                   python=platform.python_version(), torch=torch.__version__, nemo=nemo.__version__,
                   device=torch.cuda.get_device_name(), parameter_dtype=str(next(model.parameters()).dtype),
                   input_pacing='unpaced', matmul_precision=torch.get_float32_matmul_precision(), rows=[])
    write(output/'runtime.json', receipt)
    for case in cases:
        audio = args.audio_dir / (case['case']+'_conversation.wav')
        torch.cuda.synchronize()
        started = time.perf_counter()
        context = torch.autocast('cuda', dtype=torch.bfloat16) if precision == 'bf16' else nullcontext()
        with torch.inference_mode(), context:
            if mode == 'legacy_windowed':
                window_s = config['window_s']
                if 0 < config.get('whole_file_max_s', 0) >= case['audio_duration_s']:
                    window_s = max(window_s, case['audio_duration_s'] + 1)
                raw = windowed_inference(model, audio, window_s, config['overlap_s'])
                segments = normalize_max_speakers(raw, config['fold_to']) if config.get('fold_to') else [
                    dict(start=s['start_ms']/1000, end=s['end_ms']/1000, speaker=s['speaker']) for s in raw]
            else:
                annotations, tensors = model.diarize(audio=[str(audio)], batch_size=1,
                    include_tensor_outputs=True, num_workers=0, verbose=False)
                probs = tensors[0].detach().float().cpu().squeeze(0).contiguous()
                if probs.ndim != 2 or not torch.isfinite(probs).all() or (probs < 0).any() or (probs > 1).any():
                    raise ValueError('Invalid frame-by-speaker probabilities')
                probability_path = output/'probabilities'/f"{case['case']}.pt"
                probability_path.parent.mkdir(exist_ok=True)
                torch.save(probs, probability_path)
                write(output/'native'/f"{case['case']}.json", annotations)
                raw = parse_native(annotations)
                segments = (raw if mode == 'native' else probability_segments(
                    probs.numpy(), config['postprocessing'], case['audio_duration_s']))
        torch.cuda.synchronize()
        dest = output/'full_recordings'/f"{case['case']}.json"
        write(dest, dict(segments=segments))
        receipt['rows'].append(dict(case=case['case'], audio_sha256=case['audio_sha256'],
            output_sha256=sha(dest), wall_s=time.perf_counter()-started))
        write(output/'runtime.json', receipt)
        print(f"Completed {len(receipt['rows'])}/{len(cases)}", flush=True)


if __name__ == '__main__':
    main()
