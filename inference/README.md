# Run the models

## Controlled paired comparison

The controlled tables hold each NVIDIA configuration at FP32 and score the same automatic output with and without the common fold-to-two step. Use the presets in `configs/speaker-policies/` (`sortformer1`, `sortformer21`, `sortformer21_low_unpaced`, `model_x`, `model_x_streaming_unpaced`). For Model X, supply the actual model name or the evaluated checkpoint privately.

```bash
python -m inference.run --config inference/configs/speaker-policies/sortformer21.json --output private/policy-sortformer21
python -m inference.speaker_policies --output private/policy-sortformer21 --policy automatic
python -m inference.speaker_policies --output private/policy-sortformer21 --policy fold_two
```

Compare these scores with `results/speaker_policy_snapshot.json`. The saved public inputs can also be scored directly, for example with `--output data/policy_inputs/sortformer21`. `scripts/verify_speaker_policies.py` checks every public pair. The container setup below applies to both comparisons.

## Best-tested settings

The September 18 reruns use this runner directly on one NVIDIA L4, batch size 1, complete recordings. The published rows use the best measured setting per model (`configs/rerun-20260918/` for the FP32 Sortformer rows, folded to two speakers after inference; `configs/` for the BF16 native presets); every setting tried is logged in `../results/best_settings_receipt.json`.

| Row | Configuration | Input |
|---|---|---|
| Sortformer v1 | `configs/rerun-20260918/v1_windowed_fp32.json` (published row); `configs/sortformer1.json` (whole-file BF16 variant) | 180 s windows / native whole file |
| Sortformer v2.1 offline | `configs/rerun-20260918/v21_offline_fp32_a.json` (published row); `configs/sortformer21.json` (BF16 variant) | 30.4 s buffer preset |
| Sortformer v2.1 streaming | `configs/rerun-20260918/v21_low_fp32.json` (published row); `configs/sortformer21_low_unpaced.json` (BF16 variant) | 1.04 s buffer preset, unpaced |
| Model X offline | `configs/model_x.json` | 30.4 s buffer preset |
| Model X streaming | `configs/rerun-20260918/model_x_streaming_tuned_fp32.json` | 1.04 s buffer preset, unpaced, tuned decoding |

Buffer size is not measured live latency. Every run receives saved audio without wall-clock pacing. Rows marked "folded to 2" apply the historical two-speaker folding inside the runner (`fold_to: 2` in the configuration), so the documented command reproduces the published outputs; rows marked automatic keep the native speaker count.

## Environment and commands

The [Dockerfile](Dockerfile) pins the PyTorch base image, NeMo source revision and captured package versions used for the runs. Build it on a CUDA-capable machine, then mount this repository at `/work/repo`. Download the frozen audio with `git lfs pull` first.

```bash
docker build -f inference/Dockerfile -t clinical-diarization .
docker run --rm -it --gpus all --ipc host --entrypoint bash \
  -v "$PWD:/work/repo" -w /work/repo clinical-diarization

# Inside the container:
python -m inference.run --config inference/configs/rerun-20260918/v21_offline_fp32_a.json --output private/sortformer21
python -m inference.score_run --output private/sortformer21
python -m inference.compare --output private/sortformer21 --snapshot-key sortformer21
```

`run.py` verifies every audio hash before inference and checks the pinned Sortformer checkpoint hashes. It saves native segments, frame probabilities, requested settings, geometry, the loaded model configuration, package versions, GPU details, code hashes and per-recording output hashes. The [selected-run receipt](../results/best_settings_receipt.json) records the current configurations and code hashes; the [native BF16 receipt](../results/native_l4_receipt.json) records the earlier baseline. Full receipts and raw outputs stay in ignored `private/` or outside the repository. NeMo effectively clamps offline cache updates from the requested 300 to 340; the receipt records that effective value.

## Model X

Replace `"model_id": "Model X"` in either Model X preset with the actual model name, or pass `--model-id ORGANIZATION/MODEL`. All inference settings are included. For a gated model, authenticate with an account that has access.

```bash
python -m inference.run --config inference/configs/model_x.json --model-id ORGANIZATION/MODEL --output private/model-x
python -m inference.compare --output private/model-x --snapshot-key model_x
```

Use `configs/rerun-20260918/model_x_streaming_tuned_fp32.json` and snapshot key `model_x_streaming_unpaced` for streaming. No private code or ZIP is needed. The name alone downloads the current checkpoint; `--checkpoint /path/to/model.nemo` lets an authorized reviewer use the exact evaluated file. Both Model X presets were evaluated with the same checkpoint. Its identity, exact pin and individual predictions remain private; public scores are aggregate-only.

## Earlier runs

The [previous snapshot](../results/archive/2026-09-17/) and `configs/legacy/` retain the older adjusted configurations. Their folding/tuning and runtime differences should not be mixed with the current best-tested results. Other vendors' inference clients are not included; their saved outputs remain independently scoreable.
