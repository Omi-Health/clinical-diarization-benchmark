# Run the models

Two runners are included. Both verify every audio hash before inference, pin checkpoints by SHA-256 and save native
segments, frame probabilities, requested settings and the loaded geometry next to each run.

## NVIDIA models: the headline rows

The headline Nemotron 3 Diarization and Sortformer rows come from one NVIDIA L4 run on 24 September 2026 with
automatic speaker counts and an excluded same-process warmup. Reproduce them with `Dockerfile.ga` and the frozen
baseline helper; every arm selects its pinned checkpoint, precision and geometry from the run receipt in
`results/ga-20260924/snapshot.json`.

```bash
docker build -f inference/Dockerfile.ga -t clinical-diarization-ga .
docker run --rm -it --gpus all --ipc host --entrypoint bash \
  -v "$PWD:/work/repo" -w /work/repo clinical-diarization-ga

# Inside the container:
python -m inference.run_frozen_baseline --arm ga_off_bf16 --output private/nemotron3-batch
python -m inference.score_run --output private/nemotron3-batch
python -m inference.run_frozen_baseline --arm ga_stream_bf16 --output private/nemotron3-streaming
```

Arms: `ga_off_bf16`, `ga_off_fp32`, `ga_stream_bf16` (Nemotron 3), `v21_off_fp32`, `v21_stream_fp32`,
`v1_whole_bf16`, `v1_win_fp32` (Sortformer). The streaming arms replay saved audio unpaced; they do not establish live
latency. Windowed v1 output includes stitching artifacts and is not a headline automatic-count result. See the
[run record](../docs/GA_20260924.md) for the exact environment and the clean-clone execution receipt.

## Sortformer configuration study and matched speaker policies

The full configuration tables also hold Sortformer rows from `inference/run.py` on one NVIDIA L4 (18 September
2026, `Dockerfile`, batch size 1, complete recordings): each model at FP32 and BF16, with and without the
two-speaker fold. The matched speaker-policy tables score the same saved automatic output twice, unchanged and
folded, with the presets in `configs/speaker-policies/`.

```bash
docker build -f inference/Dockerfile -t clinical-diarization .
docker run --rm -it --gpus all --ipc host --entrypoint bash \
  -v "$PWD:/work/repo" -w /work/repo clinical-diarization

# Inside the container:
python -m inference.run --config inference/configs/rerun-20260918/v21_offline_fp32_a.json --output private/sortformer21
python -m inference.score_run --output private/sortformer21
python -m inference.compare --output private/sortformer21 --snapshot-key sortformer21

python -m inference.run --config inference/configs/speaker-policies/sortformer21.json --output private/policy-sortformer21
python -m inference.speaker_policies --output private/policy-sortformer21 --policy automatic
python -m inference.speaker_policies --output private/policy-sortformer21 --policy fold_two
```

| Row | Configuration | Input |
|---|---|---|
| Sortformer v1 | `configs/rerun-20260918/v1_windowed_fp32.json` (folded row); `configs/sortformer1.json` (whole-file BF16 variant) | 180 s windows / native whole file |
| Sortformer v2.1 offline | `configs/rerun-20260918/v21_offline_fp32_a.json` (folded row); `configs/sortformer21.json` (BF16 variant) | 30.4 s buffer preset |
| Sortformer v2.1 streaming | `configs/rerun-20260918/v21_low_fp32.json` (folded row); `configs/sortformer21_low_unpaced.json` (BF16 variant) | 1.04 s buffer preset, unpaced |
| Nemotron 3 Diarization | `configs/nemotron3.json` (offline), `configs/nemotron3_streaming_unpaced.json` (streaming); pinned released checkpoint | 30.4 s / 1.04 s buffer presets |

Buffer size is not measured live latency. Every run receives saved audio without wall-clock pacing. Rows marked
"folded to 2" apply the two-speaker folding inside the runner (`fold_to: 2` in the configuration); automatic rows do
not. Compare paired scores with `results/speaker_policy_snapshot.json`; the saved public inputs can also be scored
directly, for example with `--output data/policy_inputs/sortformer21`. `scripts/verify_speaker_policies.py` recomputes
every public pair.

## Environment

`Dockerfile.ga` pins the NVIDIA PyTorch base image and the NeMo Speech revision used for the 24 September run.
`Dockerfile` pins the earlier NeMo revision used for the Sortformer study; `environment-constraints.txt` lists the
captured package versions. Build either on a CUDA-capable machine and mount this repository at `/work/repo`.

Omi's runtime is not included. Omi rows in the results are aggregate-only for Nemotron 3 and Sortformer; the
Community-1 Omi-runtime outputs are public under `data/hypotheses/community1_omi_runtime`.
