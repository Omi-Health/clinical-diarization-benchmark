# Clinical Diarization Benchmark

Comparing who-spoke-when accuracy on medical conversations.

Built by [Omi Health](https://omi.health) · [Medical STT benchmark](https://github.com/Omi-Health/medical-STT-eval) · [Note safety benchmark](https://github.com/Omi-Health/medical-note-eval)

## Results

<!-- BENCHMARK:START -->

**Dataset:** 15 mock consultations, 2.4152 audio hours · **Published:** September 2026

**DER ↓** = diarization error, with ±250 ms excluded around reference boundaries. Main tables use automatic speaker counts. Full results retain zero-tolerance scores and constrained experiments.

NVIDIA baselines use their pinned released checkpoints on one L4. Hosted APIs use their public endpoints. Dates and hardware are in the [measurement record](results/RESULTS.md#measurement-record). [Run and reproduction details](docs/GA_20260924.md).

### Batch: automatic speaker counts

Same 15 whole recordings. No supplied speaker count or forced two-speaker reassignment. NVIDIA models ran locally on one L4; hosted APIs were measured through their public endpoints.

| Model | DER ↓ (±250 ms) | Correct speaker count ↑ | Measured time ↓ |
|---|---:|---:|---|
| Pyannote Precision-3 API | 2.891% | 14/15 | 18.9 s/file · API round trip |
| Nemotron 3 Diarization | 4.803% | 14/15 | 0.688 s/file · L4 |
| Pyannote Community-1 | 6.620% | 9/15 | 18.691 s/file · L4 |
| Sortformer v1, whole-file BF16 | 6.778% | 14/15 | 3.869 s/file · L4 |
| Sortformer v2.1, FP32 | 7.974% | 3/15 | 1.077 s/file · L4 |
| VibeVoice-ASR | 8.233% | 15/15 | 123 s/file · joint ASR + diarization server |

Local L4 processing and hosted API round trips have different timing scopes. Standalone model results do not represent Omi’s production service. Muse was tested in separate chunks: its result is in the shared-interval table in the full results. Precision-2 known-two and windowed/folded Sortformer runs are in the full configuration tables. Measurement dates per row are in the [measurement record](results/RESULTS.md#measurement-record).

### Batch: Omi runtime, automatic speaker counts

| Model | Baseline → Omi DER (±250 ms) | Change | Correct counts, before → after | Seconds/file, before → after | Speedup |
|---|---:|---:|---:|---:|---:|
| Nemotron 3 Diarization | 4.803% → 3.174% | -1.629 pp | 14/15 → 14/15 | 0.688 → 0.324 | 2.13× |
| Sortformer v2.1 | 7.974% → 7.487% | -0.487 pp | 3/15 → 3/15 | 1.077 → 0.854 | 1.26× |
| Pyannote Community-1 | 6.620% → 5.435% | -1.186 pp | 9/15 → 14/15 | 18.691 → 0.778 | 24.02× |

Same model weights with Omi’s proprietary runtime; no retraining. Nemotron 3 Diarization and Sortformer runtime outputs are private; Community-1 runtime outputs are public. Strict DER can worsen while collared DER improves; both scores remain in the full results.

### Streaming: automatic speaker counts

| Model / configuration | Output | DER ↓ (±250 ms) | Correct speaker count ↑ | Measured time ↓ |
|---|---|---:|---:|---|
| Pyannote live API | Delivered · paced | 3.959% | 10/15 | Latency not measured |
| Nemotron 3 Diarization + Omi | Delivered · unpaced | 4.575% | 14/15 | 7.540 s/file · L4 |
| Sortformer v2.1 + Omi | Delivered · unpaced | 6.458% | 5/15 | 38.549 s/file · L4 |
| VibeVoice 1.5B | Delivered · paced | 17.210% | 15/15 | Latency not measured |
| VibeVoice 7B | Delivered · paced | 18.032% | 13/15 | Latency not measured |
| Nemotron 3 Diarization, native preset | Retrospective · unpaced | 4.971% | 12/15 | 21.108 s/file · L4 |
| Sortformer v2.1, native preset | Retrospective · unpaced | 6.958% | 0/15 | 36.303 s/file · L4 |

Unpaced seconds/file measure processing throughput, not user-facing latency or concurrent-stream capacity. Native presets score the completed-file timeline; Omi live rows reconstruct delivered revisions. Sortformer v1 is offline-only.

All configurations, common-interval scores and alternative Omi settings are in the [full configuration tables](results/RESULTS.md#all-configurations). See the [comparison rules](docs/COMPARISON.md).

<!-- BENCHMARK:END -->

- **Scoring:** “Whole” scores complete recordings; “Common” uses the same 20 intervals for every system. ±250 ms allows timing tolerance around speech boundaries.
- **Speaker policy:** headline rows discover the count automatically; known-two and folded results are supplementary.
- **Scope:** 15 simulated consultations with VAD-refined references. Baseline hypotheses are public. Nemotron 3 and Sortformer Omi runtime rows share aggregates only; the Community-1 Omi runtime outputs are public. Omi runtime rows (a modified inference path) are listed separately and are not claims about the vanilla models.

[Full results](results/RESULTS.md) · [Methodology](docs/METHODOLOGY.md) · [L4 run scores and error counts](results/ga-20260924/snapshot.json)

## Reproduce the scores

Python 3.10+. Includes the scorer, reference timings and saved baseline outputs. `scripts/crosscheck_pyannote.py` rescores the public whole-recording outputs with pyannote.metrics as an independent check. [Inference code](inference/README.md) includes a pinned [baseline runner](docs/GA_20260924.md#reproduce) for the NVIDIA models.

```bash
GIT_LFS_SKIP_SMUDGE=1 git clone https://github.com/Omi-Health/clinical-diarization-benchmark.git
cd clinical-diarization-benchmark
python -m venv .venv
source .venv/bin/activate
pip install -e .
python scripts/verify_snapshot.py
python scripts/verify_speaker_policies.py
python scripts/verify_ga.py
```

The exact benchmark audio is available through Git LFS. See [setup, audio download and adding a comparison](docs/REPRODUCING.md).

## Data and licence

Audio and annotations derive from [PriMock57](https://github.com/babylonhealth/primock57). Code: [MIT](LICENSE). Benchmark data: [CC BY 4.0](data/LICENSE.md). See [dataset attribution](data/ATTRIBUTION.md).
