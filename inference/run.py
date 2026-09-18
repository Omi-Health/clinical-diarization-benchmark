"""Run a configured model on the frozen audio, downloading its checkpoint if needed."""
import argparse
from contextlib import nullcontext
import hashlib
import json
from pathlib import Path
import platform
import subprocess
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


def resolve_checkpoint(config, checkpoint=None, *, api=None, download=None):
    """Resolve one checkpoint by model name, or use an explicitly supplied local file."""
    revision = None
    if checkpoint is None:
        model_id = config.get('model_id', '').strip()
        if not model_id or model_id.lower() == 'model x':
            raise ValueError('Replace "Model X" in model_id with the actual model name, or pass --model-id.')
        if api is None or download is None:
            from huggingface_hub import HfApi, hf_hub_download
            api = api or HfApi()
            download = download or hf_hub_download
        info = api.model_info(model_id, revision=config.get('model_revision') or 'main')
        revision = info.sha
        if not revision:
            raise ValueError('The model repository did not return a resolved revision')
        files = [entry.rfilename for entry in info.siblings if entry.rfilename.endswith('.nemo')]
        filename = config.get('checkpoint_file')
        if filename is None:
            if len(files) != 1:
                raise ValueError('Expected one .nemo checkpoint; set checkpoint_file or pass --checkpoint')
            filename = files[0]
        elif filename not in files:
            raise ValueError('Configured checkpoint_file is missing from the model repository')
        checkpoint = Path(download(repo_id=model_id, filename=filename, revision=revision))
    checkpoint = Path(checkpoint)
    digest = sha(checkpoint)
    if config.get('checkpoint_sha256') and digest != config['checkpoint_sha256']:
        raise ValueError('Checkpoint hash mismatch')
    return checkpoint, digest, revision


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
        effective = {key: int(getattr(modules, key)) for key in geometry}
        # NeMo warns about this clamp without changing the stored attribute.
        if all(k in effective for k in ('spkcache_update_period', 'chunk_len', 'fifo_len')):
            effective['spkcache_update_period'] = min(
                max(effective['spkcache_update_period'], effective['chunk_len']),
                effective['chunk_len'] + effective['fifo_len'])
        return effective
    return {}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, required=True)
    parser.add_argument('--checkpoint', type=Path, help='Optional local checkpoint; otherwise download by model_id')
    parser.add_argument('--model-id', help='Override model_id without editing the configuration')
    parser.add_argument('--audio-dir', type=Path, default=ROOT/'data/raw_audio')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    if args.model_id:
        config['model_id'] = args.model_id
    if args.checkpoint is None and config.get('model_id', '').strip().lower() in {'', 'model x'}:
        parser.error('Replace "Model X" in the config with the actual model name, or pass --model-id.')
    mode = config['mode']
    if mode not in {'legacy_windowed', 'native', 'probabilities'}:
        raise ValueError('Unknown inference mode')
    precision = config['precision']
    if precision not in {'fp32', 'bf16'}:
        raise ValueError('precision must be fp32 or bf16')
    if config.get('fold_to') not in {None, 2}:
        raise ValueError('Only historical fold-to-two is supported')
    # Generated outputs may identify the model and belong outside tracked source/data.
    output = args.output.resolve()
    if output.is_relative_to(ROOT) and not output.is_relative_to(ROOT/'private'):
        raise ValueError('Use private/ or an output directory outside this repository')
    output.mkdir(parents=True, exist_ok=True)
    if any(output.iterdir()):
        raise ValueError('Output directory must be empty; preserve earlier runs')
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
    checkpoint, checkpoint_hash, resolved_revision = resolve_checkpoint(config, args.checkpoint)
    model = SortformerEncLabelModel.restore_from(str(checkpoint), map_location='cpu', strict=config['strict'])
    dtype = torch.bfloat16 if precision == 'bf16' else torch.float32
    model = model.to(device='cuda', dtype=dtype).eval()
    geometry = configure(model, config)
    from omegaconf import OmegaConf
    write(output/'model_config.json', OmegaConf.to_container(model.cfg, resolve=True))
    (output/'environment.txt').write_text(subprocess.check_output([__import__('sys').executable, '-m', 'pip', 'freeze'], text=True))
    (output/'gpu.txt').write_text(subprocess.check_output(['nvidia-smi'], text=True))
    receipt = dict(configuration=config, effective_geometry=geometry,
                   checkpoint_sha256=checkpoint_hash, resolved_model_revision=resolved_revision,
                   runner_sha256=sha(__file__),
                   processing_sha256=sha(Path(__file__).with_name('processing.py')),
                   manifest_sha256=sha(ROOT/'data/manifest.json'),
                   python=platform.python_version(), torch=torch.__version__, nemo=nemo.__version__,
                   device=torch.cuda.get_device_name(), parameter_dtype=str(next(model.parameters()).dtype),
                   input_pacing='unpaced', matmul_precision=torch.get_float32_matmul_precision(), rows=[])
    write(output/'runtime.json', receipt)
    for case in cases:
        receipt['current_case'] = case['case']
        write(output/'runtime.json', receipt)
        audio = args.audio_dir / (case['case']+'_conversation.wav')
        torch.cuda.synchronize()
        torch.cuda.reset_peak_memory_stats()
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
            output_sha256=sha(dest), wall_s=time.perf_counter()-started,
            peak_gpu_allocated_bytes=torch.cuda.max_memory_allocated(),
            hypothesis_speakers=len({s['speaker'] for s in segments})))
        write(output/'runtime.json', receipt)
        print(f"Completed {len(receipt['rows'])}/{len(cases)}", flush=True)
    receipt.pop('current_case', None)
    receipt['completed'] = True
    write(output/'runtime.json', receipt)


if __name__ == '__main__':
    main()
