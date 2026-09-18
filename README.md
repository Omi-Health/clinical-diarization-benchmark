# Clinical Diarization Benchmark

Comparing who-spoke-when accuracy on medical conversations.

Built by [Omi Health](https://omi.health) · [Medical STT benchmark](https://github.com/Omi-Health/medical-STT-eval) · [Note safety benchmark](https://github.com/Omi-Health/medical-note-eval)

## Results

<!-- BENCHMARK:START -->

**Dataset:** 15 mock consultations, 2.4152 audio hours · **Updated:** 2026-09-19

**DER ↓** = speaker diarization error. Ranked by common-interval DER at ±250 ms.

### Best-tested settings and speed

Best tested configurations on this dataset, with measured speed. Speaker constraints and decoding differ by row; the controlled comparison below isolates speaker policy.

Speed scopes differ: local L4 processing, API round trips, or joint ASR plus diarization. See [timing details](docs/METHODOLOGY.md#speed).

#### Batch / offline

| System | Speaker policy | Whole DER, zero | Whole DER, ±250 ms | Common DER, zero | Common DER, ±250 ms | Whole-file count accuracy | Speed |
|---|---|---:|---:|---:|---:|---:|---|
| pyannoteAI Precision-2 API | Known 2 | 11.004% | 2.823% | 10.986% | 2.824% | constrained | 12 s/file, API round trip |
| Sortformer v1, 180 s windows, FP32 | Folded to 2 after inference | 12.706% | 3.159% | 12.706% | 3.159% | constrained | 1.7 s/file (274×), L4 batch |
| Sortformer v2.1, 30.4 s preset, FP32 | Folded to 2 after inference | 11.407% | 3.945% | 11.407% | 3.946% | constrained | 1.1 s/file (402×), L4 batch |
| Model X, 30.4 s preset, BF16 | Automatic | 12.593% | 4.786% | 12.593% | 4.787% | 80.0% | 0.7 s/file (768×), L4 batch |
| pyannoteAI Community-1, whole-file | Known 2; historical folding to 2 | 15.856% | 6.323% | 15.855% | 6.325% | constrained | 18.5 s/file (31×), L4 batch |
| VibeVoice-ASR, native batch | Automatic | 24.191% | 8.233% | 24.191% | 8.235% | 100.0% | 123 s/file, joint ASR+diarization server |
| Meta Muse Voice Transcribe | Automatic per request | 29.169%\* | 13.042%\* | 29.169% | 13.042% | 90.0%\* | 92 s/request, API round trip |

\* Muse's starred values are interval results, not whole-recording results; count accuracy is 18/20 intervals.

#### Streaming diarization

| System | Input pacing | Speaker policy | Whole DER, zero | Whole DER, ±250 ms | Common DER, zero | Common DER, ±250 ms | Whole-file count accuracy | Speed |
|---|---|---|---:|---:|---:|---:|---:|---|
| pyannoteAI live API | Real-time paced | Automatic | 10.515% | 3.959% | 10.515% | 3.960% | 66.7% | — |
| Model X, 1.04 s preset, unpaced, tuned decoding, FP32 | Unpaced | Tuned; top 2 speakers retained | 12.567% | 4.275% | 12.567% | 4.277% | constrained | 19.8 s/file (29×), L4 batch |
| Sortformer v2.1, 1.04 s preset, unpaced, FP32 | Unpaced | Folded to 2 after inference | 12.496% | 4.815% | 12.496% | 4.816% | constrained | 36.4 s/file (16×), L4 batch |
| VibeVoice streaming 1.5B, paced | Real-time paced | Automatic | 32.947% | 17.210% | 32.947% | 17.215% | 100.0% | — |
| VibeVoice streaming 7B, paced | Real-time paced | Automatic | 33.808% | 18.032% | 33.808% | 18.036% | 86.7% | — |

**Speed in this table:** unpaced replay of the chunk loop on one L4, batch size 1; it is throughput of the streaming preset on saved audio, not live latency.

**Pacing:** real-time = normal speaking speed; unpaced = processed without waiting. Scores measure accuracy, not live latency.

### Controlled speaker-policy comparison

Each pair uses the same saved automatic output, unchanged or folded to at most two speakers with the same function. NVIDIA pairs use FP32 and native decoding (v1 uses 180 s windows).

#### Batch / offline

##### Automatic speaker count

| System | Whole DER, zero | Whole DER, ±250 ms | Common DER, zero | Common DER, ±250 ms | Count accuracy |
|---|---:|---:|---:|---:|---:|
| Model X, 30.4 s preset, FP32 | 12.594% | 4.787% | 12.594% | 4.789% | 80.0% |
| pyannoteAI Community-1, automatic inference | 16.243% | 6.620% | 16.242% | 6.622% | 60.0% |
| Sortformer v2.1, 30.4 s preset, FP32 | 15.768% | 7.974% | 14.543% | 6.832% | 20.0% |
| VibeVoice-ASR, native batch | 24.191% | 8.233% | 24.191% | 8.235% | 100.0% |
| Meta Muse Voice Transcribe | 29.169%\* | 13.042%\* | 29.169% | 13.042% | 90.0%\* |
| Sortformer v1, 180 s windows, FP32 | n/a (windowed) | n/a (windowed) | n/a (windowed) | n/a (windowed) | n/a (windowed) |

##### Same two-speaker post-processing

| System | Whole DER, zero | Whole DER, ±250 ms | Common DER, zero | Common DER, ±250 ms | Count accuracy |
|---|---:|---:|---:|---:|---:|
| Sortformer v1, 180 s windows, FP32 | 12.706% | 3.159% | 12.706% | 3.159% | constrained |
| Sortformer v2.1, 30.4 s preset, FP32 | 11.407% | 3.945% | 11.407% | 3.946% | constrained |
| Model X, 30.4 s preset, FP32 | 12.590% | 4.787% | 12.590% | 4.789% | constrained |
| pyannoteAI Community-1, automatic inference | 16.089% | 6.574% | 16.087% | 6.575% | constrained |
| VibeVoice-ASR, native batch | 24.191% | 8.233% | 24.191% | 8.235% | constrained |
| Meta Muse Voice Transcribe | 29.157%\* | 13.042%\* | 29.157% | 13.042% | constrained |

\* Muse: 20 separate request intervals, not whole recordings. V1 automatic results are n/a: window stitching adds labels, so this is not a model-only counting result. Raw scores and the whole-file variant remain in the settings log.

#### Streaming diarization

##### Automatic speaker count

| System | Input pacing | Whole DER, zero | Whole DER, ±250 ms | Common DER, zero | Common DER, ±250 ms | Count accuracy |
|---|---|---:|---:|---:|---:|---:|
| pyannoteAI live API | Real-time paced | 10.515% | 3.959% | 10.515% | 3.960% | 66.7% |
| Model X, 1.04 s preset, FP32, native decoding | Unpaced | 12.754% | 4.947% | 12.754% | 4.948% | 46.7% |
| Sortformer v2.1, 1.04 s preset, unpaced, FP32 | Unpaced | 14.841% | 6.958% | 14.841% | 6.960% | 0.0% |
| VibeVoice streaming 1.5B, paced | Real-time paced | 32.947% | 17.210% | 32.947% | 17.215% | 100.0% |
| VibeVoice streaming 7B, paced | Real-time paced | 33.808% | 18.032% | 33.808% | 18.036% | 86.7% |

##### Same two-speaker post-processing

| System | Input pacing | Whole DER, zero | Whole DER, ±250 ms | Common DER, zero | Common DER, ±250 ms | Count accuracy |
|---|---|---:|---:|---:|---:|---:|
| pyannoteAI live API | Real-time paced | 10.092% | 3.592% | 10.092% | 3.593% | constrained |
| Sortformer v2.1, 1.04 s preset, unpaced, FP32 | Unpaced | 12.496% | 4.815% | 12.496% | 4.816% | constrained |
| Model X, 1.04 s preset, FP32, native decoding | Unpaced | 12.669% | 4.865% | 12.669% | 4.866% | constrained |
| VibeVoice streaming 1.5B, paced | Real-time paced | 32.947% | 17.210% | 32.947% | 17.215% | constrained |
| VibeVoice streaming 7B, paced | Real-time paced | 33.808% | 18.032% | 33.808% | 18.036% | constrained |

Unpaced = saved audio processed without waiting. Two-speaker correction uses the complete output after the stream, not a live speaker-count decision. These scores do not measure latency.

Additional unpaced VibeVoice runs and all settings are in the [detailed results](results/RESULTS.md).

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
