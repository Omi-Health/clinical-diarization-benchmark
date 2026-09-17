# Inference code

Review the model calls, window stitching and postprocessing used by the benchmark. These are standalone adapters extracted from our evaluation paths; service deployment and Omi's identity resolver are excluded.

| Published row | Configuration | Processing |
|---|---|---|
| Sortformer v1 | `configs/sortformer1.json` | 180 s windows, 12 s overlap, overlap stitching, fold to two speakers |
| Sortformer v2.1, whole-file | `configs/sortformer21.json` | September 7 whole-file run, explicit offline geometry, fold to two speakers |
| Sortformer v2.1, streaming preset | `configs/sortformer21_low_unpaced.json` | 1.04 s preset, unpaced file input, fold to two speakers |
| Model X, offline / streaming | Supplied privately | Generic native output or probability postprocessing; no private model ID or preset is embedded in the code |

`run.py` loads a checkpoint supplied with `--checkpoint`. `processing.py` contains timestamp parsing, stitching, normalization and configurable probability decoding. `compare.py` checks a rerun against the published scores without modifying them.

## Run

Use a CUDA environment with PyTorch and a compatible `nemo_toolkit[asr]`. The CPU scoring installation alone cannot run inference. Obtain the Sortformer weights at the model ID and revision in the selected JSON; the runner verifies the checkpoint SHA-256. Model X requires separately supplied authorized weights and settings.

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

For a privately supplied preset, pass its JSON to `--config` instead. Configurations, probability tensors and runtime receipts may identify a confidential model; keep them private. The runner accepts only an empty output directory outside the repository or under ignored `private/`.

## Validation and limits

- Extracted normalization reproduces the published whole-recording outputs for all 45 Sortformer cases. Configurable probability decoding reproduces all 15 archived Model X streaming outputs. Both Model X score panels were checked privately against saved per-case counts.
- CPU tests cover window slicing, speaker stitching, millisecond conversion, threshold/gap behavior and speaker dropping versus folding.
- No new GPU inference was run while extracting this code. Historical software versions are not fully pinned. A new run may differ; the comparison command reports differences rather than overwriting results.
- The whole-file v2.1 row uses the September 7 offline preset, not the earlier checkpoint-default run. The saved environment records Python 3.11.13, PyTorch 2.8.0+cu128, CUDA 12.8 and an L4, but no NeMo revision. Its requested update period was 300; the recorded effective value was 340. Requested and effective settings are captured again on rerun.
- Model X settings and outputs remain private. Without them, its published aggregates cannot be independently reproduced. The older streaming run lacks a recorded checkpoint revision/hash; saved-output parity is stronger evidence here than exact fresh-inference reproducibility.
- Every adapter here receives saved audio without real-time pacing. The pyannote and VibeVoice inference clients are not included.
