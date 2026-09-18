# Clinical Diarization Benchmark

Comparing who-spoke-when accuracy on medical conversations.

Built by [Omi Health](https://omi.health) · [Medical STT benchmark](https://github.com/Omi-Health/medical-STT-eval) · [Note safety benchmark](https://github.com/Omi-Health/medical-note-eval)

## Results

<!-- BENCHMARK:START -->

**Dataset:** 15 mock consultations, 2.4152 audio hours · **Updated:** 2026-09-19

**DER ↓** = speaker diarization error. Ranked by common-interval DER at ±250 ms.

**Matched policies:** each pair uses the same saved output. The second table keeps the two most-active labels and folds extras into the second. NVIDIA pairs use FP32; inference settings stay fixed between the two policies.

### Batch / offline

#### Automatic speaker count

| System | Whole DER, zero | Whole DER, ±250 ms | Common DER, zero | Common DER, ±250 ms | Count accuracy |
|---|---:|---:|---:|---:|---:|
| Model X, 30.4 s preset, FP32 | 12.594% | 4.787% | 12.594% | 4.789% | 80.0% |
| Sortformer v1, 180 s windows, FP32 | 18.555% | 9.474% | 15.921% | 6.602% | 33.3% |
| pyannoteAI Community-1, automatic inference | 16.243% | 6.620% | 16.242% | 6.622% | 60.0% |
| Sortformer v2.1, 30.4 s preset, FP32 | 15.768% | 7.974% | 14.543% | 6.832% | 20.0% |
| VibeVoice-ASR, native batch | 24.191% | 8.233% | 24.191% | 8.235% | 100.0% |
| Meta Muse Voice Transcribe | 29.169%\* | 13.042%\* | 29.169% | 13.042% | 90.0%\* |

#### Same two-speaker post-processing

| System | Whole DER, zero | Whole DER, ±250 ms | Common DER, zero | Common DER, ±250 ms | Count accuracy |
|---|---:|---:|---:|---:|---:|
| Sortformer v1, 180 s windows, FP32 | 12.706% | 3.159% | 12.706% | 3.159% | constrained |
| Sortformer v2.1, 30.4 s preset, FP32 | 11.407% | 3.945% | 11.407% | 3.946% | constrained |
| Model X, 30.4 s preset, FP32 | 12.590% | 4.787% | 12.590% | 4.789% | constrained |
| pyannoteAI Community-1, automatic inference | 16.089% | 6.574% | 16.087% | 6.575% | constrained |
| VibeVoice-ASR, native batch | 24.191% | 8.233% | 24.191% | 8.235% | constrained |
| Meta Muse Voice Transcribe | 29.157%\* | 13.042%\* | 29.157% | 13.042% | constrained |

\* Muse: 20 separate request intervals, not whole recordings. V1 automatic counts include window-stitching errors.

### Streaming diarization

#### Automatic speaker count

| System | Input pacing | Whole DER, zero | Whole DER, ±250 ms | Common DER, zero | Common DER, ±250 ms | Count accuracy |
|---|---|---:|---:|---:|---:|---:|
| pyannoteAI live API | Real-time paced | 10.515% | 3.959% | 10.515% | 3.960% | 66.7% |
| Model X, 1.04 s preset, FP32, native decoding | Unpaced | 12.754% | 4.947% | 12.754% | 4.948% | 46.7% |
| Sortformer v2.1, 1.04 s preset, unpaced, FP32 | Unpaced | 14.841% | 6.958% | 14.841% | 6.960% | 0.0% |
| VibeVoice streaming 1.5B, paced | Real-time paced | 32.947% | 17.210% | 32.947% | 17.215% | 100.0% |
| VibeVoice streaming 7B, paced | Real-time paced | 33.808% | 18.032% | 33.808% | 18.036% | 86.7% |

#### Same two-speaker post-processing

| System | Input pacing | Whole DER, zero | Whole DER, ±250 ms | Common DER, zero | Common DER, ±250 ms | Count accuracy |
|---|---|---:|---:|---:|---:|---:|
| pyannoteAI live API | Real-time paced | 10.092% | 3.592% | 10.092% | 3.593% | constrained |
| Sortformer v2.1, 1.04 s preset, unpaced, FP32 | Unpaced | 12.496% | 4.815% | 12.496% | 4.816% | constrained |
| Model X, 1.04 s preset, FP32, native decoding | Unpaced | 12.669% | 4.865% | 12.669% | 4.866% | constrained |
| VibeVoice streaming 1.5B, paced | Real-time paced | 32.947% | 17.210% | 32.947% | 17.215% | constrained |
| VibeVoice streaming 7B, paced | Real-time paced | 33.808% | 18.032% | 33.808% | 18.036% | constrained |

Unpaced = saved audio processed without waiting. Two-speaker correction uses the complete output after the stream, not a live speaker-count decision. These scores do not measure latency.

[Other settings and timings](results/RESULTS.md#earlier-selected-settings-and-timings) include Precision-2’s known-two API run and the earlier tuned Model X streaming result. Additional unpaced VibeVoice pairs are in the detailed results.

<!-- BENCHMARK:END -->

- **Scoring:** “Whole” scores complete recordings; “Common” uses the same 20 intervals for every system. ±250 ms allows timing tolerance around speech boundaries.
- **Speaker policy:** some runs use the known two-speaker count. “Constrained” does not measure automatic speaker counting.
- **Scope:** 15 simulated consultations with VAD-refined references. Model X is anonymized and shares aggregates only. Omi's proprietary runtime is not included.

[Full results](results/RESULTS.md) · [Methodology](docs/METHODOLOGY.md) · [Scores and error counts](results/speaker_policy_snapshot.json)

## Reproduce the scores

Python 3.10+. Includes the scorer, reference timings and saved baseline outputs. `scripts/crosscheck_pyannote.py` rescores the public whole-recording outputs with pyannote.metrics as an independent check. [Inference code](inference/README.md) is included for Sortformer and configurable Model X runs; for Model X, replace the placeholder model name in its preset and run; no private ZIP is needed.

```bash
GIT_LFS_SKIP_SMUDGE=1 git clone https://github.com/Omi-Health/clinical-diarization-benchmark.git
cd clinical-diarization-benchmark
python -m venv .venv
source .venv/bin/activate
pip install -e .
python scripts/verify_snapshot.py
python scripts/verify_speaker_policies.py
```

The exact benchmark audio is available through Git LFS. See [setup, audio download and adding a comparison](docs/REPRODUCING.md).

## Data and licence

Audio and annotations derive from [PriMock57](https://github.com/babylonhealth/primock57). Code: [MIT](LICENSE). Benchmark data: [CC BY 4.0](data/LICENSE.md). See [dataset attribution](data/ATTRIBUTION.md).
