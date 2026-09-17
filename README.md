# Clinical Diarization Benchmark

Comparing who-spoke-when accuracy on medical conversations.

Built by [Omi Health](https://omi.health) · [Medical STT benchmark](https://github.com/Omi-Health/medical-STT-eval) · [Note safety benchmark](https://github.com/Omi-Health/medical-note-eval)

## Results

<!-- BENCHMARK:START -->

**Dataset**: PriMock57 (15 mock consultations, 2.4152 audio hours) | **Configurations shown**: 12 | **Updated**: 2026-09-17

**DER ↓** = speaker diarization error; lower is better. Ranked by common-interval DER at ±250 ms.

### Batch / offline

| System | Speaker policy | Whole DER, zero | Whole DER, ±250 ms | Common DER, zero | Common DER, ±250 ms | Whole-file count accuracy |
|---|---|---:|---:|---:|---:|---:|
| pyannoteAI Precision-2 API | Known 2 | 11.004% | 2.823% | 10.986% | 2.824% | constrained |
| Sortformer v1, 180s windows | Folded to 2 after inference | 12.706% | 3.157% | 12.706% | 3.158% | constrained |
| Sortformer v2.1, whole-file | Folded to 2 after inference | 12.173% | 3.610% | 12.173% | 3.611% | constrained |
| Model X | Automatic | 12.589% | 4.786% | 12.589% | 4.787% | 80.0% |
| pyannoteAI Community-1, whole-file | Known 2; historical folding to 2 | 15.856% | 6.323% | 15.855% | 6.325% | constrained |
| VibeVoice-ASR, native batch | Automatic | 24.191% | 8.233% | 24.191% | 8.235% | 100.0% |
| Meta Muse Voice Transcribe | Automatic per request | 29.169%\* | 13.042%\* | 29.169% | 13.042% | 90.0%\* |

\* Muse's starred values are interval results, not whole-recording results; count accuracy is 18/20 intervals.

### Streaming diarization

| System | Input pacing | Speaker policy | Whole DER, zero | Whole DER, ±250 ms | Common DER, zero | Common DER, ±250 ms | Whole-file count accuracy |
|---|---|---|---:|---:|---:|---:|---:|
| pyannoteAI live API | Real-time paced | Automatic | 10.515% | 3.959% | 10.515% | 3.960% | 66.7% |
| Model X, streaming preset, unpaced (tuned) | Unpaced | Tuned; top 2 speakers retained | 12.566% | 4.271% | 12.566% | 4.272% | constrained |
| Sortformer v2.1, 1.04 s preset, unpaced | Unpaced | Folded to 2 after inference | 13.031% | 5.397% | 13.031% | 5.398% | constrained |
| VibeVoice streaming 1.5B, paced | Real-time paced | Automatic | 32.947% | 17.210% | 32.947% | 17.215% | 100.0% |
| VibeVoice streaming 7B, paced | Real-time paced | Automatic | 33.808% | 18.032% | 33.808% | 18.036% | 86.7% |

**Pacing:** real-time = normal speaking speed; unpaced = processed without waiting. Scores measure accuracy, not live latency.

2 additional VibeVoice unpaced runs are available in the [detailed results](results/RESULTS.md#streaming-diarization).

<!-- BENCHMARK:END -->

- **Scoring:** “Whole” scores complete recordings; “Common” uses the same 20 intervals for every system. ±250 ms allows timing tolerance around speech boundaries.
- **Speaker policy:** some runs use the known two-speaker count. “Constrained” does not measure automatic speaker counting.
- **Scope:** 15 simulated consultations with VAD-refined references. Model X is anonymized and shares aggregates only. Omi's proprietary runtime is not included.

[Full results](results/RESULTS.md) · [Methodology](docs/METHODOLOGY.md) · [Scores and error counts](results/snapshot.json)

## Reproduce the scores

Python 3.10+. Includes the scorer, reference timings and saved baseline outputs. Model inference runners are not included; Model X's individual outputs are private.

```bash
GIT_LFS_SKIP_SMUDGE=1 git clone https://github.com/Omi-Health/clinical-diarization-benchmark.git
cd clinical-diarization-benchmark
python -m venv .venv
source .venv/bin/activate
pip install -e .
python scripts/verify_snapshot.py
```

The exact benchmark audio is available through Git LFS. See [setup, audio download and adding a comparison](docs/REPRODUCING.md).

## Data and licence

Audio and annotations derive from [PriMock57](https://github.com/babylonhealth/primock57). Code: [MIT](LICENSE). Benchmark data: [CC BY 4.0](data/LICENSE.md). See [dataset attribution](data/ATTRIBUTION.md).
