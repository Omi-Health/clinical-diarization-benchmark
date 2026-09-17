# Inference code

Review the model calls, window stitching and postprocessing used by the benchmark. These are standalone adapters extracted from our evaluation paths; service deployment and Omi's identity resolver are excluded.

| Published row | Configuration | Processing |
|---|---|---|
| Sortformer v1 | `configs/sortformer1.json` | 180 s windows, 12 s overlap, overlap stitching, fold to two speakers |
| Sortformer v2.1, whole-file | `configs/sortformer21.json` | September 7 whole-file run, explicit offline geometry, fold to two speakers |
| Sortformer v2.1, streaming preset | `configs/sortformer21_low_unpaced.json` | 1.04 s preset, unpaced file input, fold to two speakers |
| Model X, offline | `configs/model_x.json` | Native output; automatic speaker count |
| Model X, streaming | `configs/model_x_streaming_unpaced.json` | Unpaced streaming preset; tuned decoding, top two speakers retained |

`run.py` downloads the checkpoint by `model_id`, or loads a local file supplied with `--checkpoint`. `processing.py` contains timestamp parsing, stitching, normalization and configurable probability decoding. `compare.py` checks a rerun against the published scores without modifying them.

## Run

Use a CUDA environment with PyTorch and a compatible `nemo_toolkit[asr]`. The CPU scoring installation alone cannot run inference. Obtain the Sortformer weights at the model ID and revision in the selected JSON; the runner verifies the checkpoint SHA-256. For a gated model, sign in to Hugging Face with an account that has access.

From the repository root, after downloading the audio with Git LFS:

```bash
python -m inference.run \
  --config inference/configs/sortformer21.json \
  --checkpoint /path/to/checkpoint.nemo \
  --output private/rerun-sortformer21

python -m inference.compare \
  --output private/rerun-sortformer21 \
  --snapshot-key sortformer21
```

## Model X: change the name and run

Replace `"model_id": "Model X"` in `configs/model_x.json` with the actual Hugging Face model name. All inference settings are already included. Then run from the repository root:

```bash
python -m inference.run --config inference/configs/model_x.json --output private/model-x-offline
python -m inference.compare --output private/model-x-offline --snapshot-key model_x
```

For streaming, make the same name change in `configs/model_x_streaming_unpaced.json` and use that file with `--snapshot-key model_x_streaming_unpaced`. Alternatively, pass `--model-id ORGANIZATION/MODEL` without editing either file. No separate configuration or ZIP is needed.

The runner discovers the checkpoint filename and records the downloaded revision/hash. Model X downloads the current revision; changing the name enables inference but does not pin the historical checkpoint or guarantee identical scores. Generated outputs and receipts may identify the model; they stay under ignored `private/` or outside the repository.

## Validation and limits

- Extracted normalization reproduces the published whole-recording outputs for all 45 Sortformer cases. Configurable probability decoding reproduces all 15 archived Model X streaming outputs. Both Model X score panels were checked privately against saved per-case counts.
- CPU tests cover window slicing, speaker stitching, millisecond conversion, threshold/gap behavior and speaker dropping versus folding.
- Rerun check, 2026-09-17 (NVIDIA L4, Python 3.11.13, PyTorch 2.8.0+cu128, NeMo 2.7.3, pinned checkpoints): `sortformer1.json` reproduces the published Sortformer v1 row (±250 ms identical, zero collar within 2 frames). `sortformer21.json` does **not** reproduce the published Sortformer v2.1 row: the September 7 run went through Omi's production runtime, which merges same-speaker gaps of up to about 0.5 s after inference and clamps `spkcache_update_period` to `chunk_len` (effective 340); this adapter does neither. Its raw output gives 11.317 % / 3.866 % (zero / ±250 ms) against the published 12.173 % / 3.610 %, with every rerun segment contained in a published one. Treat the published v2.1 row as the product path and the adapter as the raw model path until the merge is added here.
- Historical software versions are not fully pinned. A new run may differ; the comparison command reports differences rather than overwriting results.
- The whole-file v2.1 row uses the September 7 offline preset, not the earlier checkpoint-default run. The saved environment records Python 3.11.13, PyTorch 2.8.0+cu128, CUDA 12.8 and an L4, but no NeMo revision. Its requested update period was 300; the recorded effective value was 340. Requested and effective settings are captured again on rerun.
- Model X presets are public; its name and historical individual outputs remain private. The comparison command checks newly generated outputs against published aggregates. No fresh GPU inference was run for the name-based loading change. The older streaming run lacks a recorded checkpoint revision/hash.
- Every adapter here receives saved audio without real-time pacing. The pyannote and VibeVoice inference clients are not included.
