"""Reproduce the 24 September native baselines, with explicit excluded warmup.

No Omi graph/runtime code, folding, or tuned probability decoder is used.
"""
import argparse
from contextlib import nullcontext
import json
from pathlib import Path
import time

from .run import configure, resolve_checkpoint, sha, write, windowed_inference
from .processing import parse_native

ROOT = Path(__file__).resolve().parents[1]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--arm', required=True, choices=['ga_off_bf16', 'ga_off_fp32', 'ga_stream_bf16',
                   'v21_off_fp32', 'v21_stream_fp32', 'v1_whole_bf16', 'v1_win_fp32'])
    p.add_argument('--audio-dir', type=Path, default=ROOT/'data/raw_audio')
    p.add_argument('--checkpoint', type=Path)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    archive = json.loads((ROOT/'results/ga-20260924/snapshot.json').read_text())
    receipt = archive['arms'][args.arm]['receipt']
    config = {'model_id': receipt['model_id'], 'model_revision': receipt['model_revision'],
              'checkpoint_sha256': receipt['checkpoint_sha256'], 'geometry': receipt['geometry_requested']}
    output = args.output.resolve()
    if output.is_relative_to(ROOT) and not output.is_relative_to(ROOT/'private'):
        raise ValueError('Use private/ or an output directory outside this repository')
    output.mkdir(parents=True, exist_ok=True)
    if any(output.iterdir()):
        raise ValueError('Keep earlier outputs: the output directory must be empty')
    cases = json.loads((ROOT/'data/manifest.json').read_text())['recordings']
    for case in cases:
        assert sha(args.audio_dir/(case['case']+'_conversation.wav')) == case['audio_sha256']
    import numpy as np
    import torch
    from nemo.collections.asr.models import SortformerEncLabelModel
    if not torch.cuda.is_available():
        raise RuntimeError('CUDA is required')
    torch.manual_seed(42)
    torch.set_float32_matmul_precision('highest')
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
    checkpoint, digest, _ = resolve_checkpoint(config, args.checkpoint)
    model = SortformerEncLabelModel.restore_from(str(checkpoint), map_location='cpu', strict=True).to('cuda').eval()
    bf16 = receipt['args']['precision'] == 'bf16'
    if bf16:
        model = model.to(torch.bfloat16)
    geometry = configure(model, config)
    model.async_streaming = False
    model.async_pad_to_max = False
    windowed = receipt['args']['geometry'] == 'windowed'

    def infer(audio):
        context = torch.autocast('cuda', dtype=torch.bfloat16) if bf16 else nullcontext()
        with torch.inference_mode(), context:
            if windowed:
                raw = windowed_inference(model, audio, 180, 12)
                return [dict(start=s['start_ms']/1000, end=s['end_ms']/1000, speaker=s['speaker']) for s in raw], None
            annotations, tensors = model.diarize(audio=[str(audio)], batch_size=1,
                num_workers=0, verbose=False, include_tensor_outputs=True)
            return annotations[0], tensors[0].detach().float().cpu().squeeze(0).numpy()

    infer(args.audio_dir/(cases[0]['case']+'_conversation.wav'))
    torch.cuda.synchronize()
    result = dict(arm=args.arm, checkpoint_sha256=digest, geometry_effective=geometry,
                  warmup='first whole recording, excluded', torch=torch.__version__,
                  device=torch.cuda.get_device_name(), timing='inference excludes output serialization; native parsing is untimed', rows=[])
    for case in cases:
        torch.cuda.synchronize()
        started = time.perf_counter()
        native, probs = infer(args.audio_dir/(case['case']+'_conversation.wav'))
        torch.cuda.synchronize()
        elapsed = time.perf_counter()-started
        segments = native if windowed else parse_native([native])
        write(output/'full_recordings'/(case['case']+'.json'), {'segments': segments})
        write(output/'native'/(case['case']+'.json'), native)
        if probs is not None:
            (output/'probabilities').mkdir(exist_ok=True)
            np.save(output/'probabilities'/(case['case']+'.npy'), probs)
        result['rows'].append(dict(case=case['case'], wall_s=elapsed))
        write(output/'runtime.json', result)
        print(f"Completed {len(result['rows'])}/{len(cases)}", flush=True)
    result['completed'] = True
    write(output/'runtime.json', result)


if __name__ == '__main__':
    main()
