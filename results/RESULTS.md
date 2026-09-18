# Diarization results

Same 15 PriMock consultations, 2.4152 audio hours. Updated 2026-09-19.

Each pair scores the same automatic inference output, unchanged or folded to at most two speakers with the same public function. NVIDIA pairs use FP32 and native decoding (v1 uses 180 s windows). Ranked by common-interval DER at ±250 ms. These are controlled speaker-policy comparisons, not best-setting claims.

Omi’s proprietary runtime is not included. Model X remains aggregate-only.

## Batch / offline

### Automatic speaker count

| System | Whole DER, zero | Whole DER, ±250 ms | Common DER, zero | Common DER, ±250 ms | Count accuracy |
|---|---:|---:|---:|---:|---:|
| Model X, 30.4 s preset, FP32 | 12.594% | 4.787% | 12.594% | 4.789% | 80.0% |
| Sortformer v1, 180 s windows, FP32 | 18.555% | 9.474% | 15.921% | 6.602% | 33.3% |
| pyannoteAI Community-1, automatic inference | 16.243% | 6.620% | 16.242% | 6.622% | 60.0% |
| Sortformer v2.1, 30.4 s preset, FP32 | 15.768% | 7.974% | 14.543% | 6.832% | 20.0% |
| VibeVoice-ASR, native batch | 24.191% | 8.233% | 24.191% | 8.235% | 100.0% |
| Meta Muse Voice Transcribe | 29.169%\* | 13.042%\* | 29.169% | 13.042% | 90.0%\* |

### Same two-speaker post-processing

| System | Whole DER, zero | Whole DER, ±250 ms | Common DER, zero | Common DER, ±250 ms | Count accuracy |
|---|---:|---:|---:|---:|---:|
| Sortformer v1, 180 s windows, FP32 | 12.706% | 3.159% | 12.706% | 3.159% | constrained |
| Sortformer v2.1, 30.4 s preset, FP32 | 11.407% | 3.945% | 11.407% | 3.946% | constrained |
| Model X, 30.4 s preset, FP32 | 12.590% | 4.787% | 12.590% | 4.789% | constrained |
| pyannoteAI Community-1, automatic inference | 16.089% | 6.574% | 16.087% | 6.575% | constrained |
| VibeVoice-ASR, native batch | 24.191% | 8.233% | 24.191% | 8.235% | constrained |
| Meta Muse Voice Transcribe | 29.157%\* | 13.042%\* | 29.157% | 13.042% | constrained |

\* Muse: 20 separate request intervals, not whole recordings. V1 automatic counts include window-stitching errors.

## Streaming diarization

### Automatic speaker count

| System | Input pacing | Whole DER, zero | Whole DER, ±250 ms | Common DER, zero | Common DER, ±250 ms | Count accuracy |
|---|---|---:|---:|---:|---:|---:|
| pyannoteAI live API | Real-time paced | 10.515% | 3.959% | 10.515% | 3.960% | 66.7% |
| Model X, 1.04 s preset, FP32, native decoding | Unpaced | 12.754% | 4.947% | 12.754% | 4.948% | 46.7% |
| Sortformer v2.1, 1.04 s preset, unpaced, FP32 | Unpaced | 14.841% | 6.958% | 14.841% | 6.960% | 0.0% |
| VibeVoice streaming 7B, unpaced | Unpaced | 32.627% | 16.838% | 32.627% | 16.842% | 93.3% |
| VibeVoice streaming 1.5B, unpaced | Unpaced | 32.669% | 16.952% | 32.669% | 16.956% | 100.0% |
| VibeVoice streaming 1.5B, paced | Real-time paced | 32.947% | 17.210% | 32.947% | 17.215% | 100.0% |
| VibeVoice streaming 7B, paced | Real-time paced | 33.808% | 18.032% | 33.808% | 18.036% | 86.7% |

### Same two-speaker post-processing

| System | Input pacing | Whole DER, zero | Whole DER, ±250 ms | Common DER, zero | Common DER, ±250 ms | Count accuracy |
|---|---|---:|---:|---:|---:|---:|
| pyannoteAI live API | Real-time paced | 10.092% | 3.592% | 10.092% | 3.593% | constrained |
| Sortformer v2.1, 1.04 s preset, unpaced, FP32 | Unpaced | 12.496% | 4.815% | 12.496% | 4.816% | constrained |
| Model X, 1.04 s preset, FP32, native decoding | Unpaced | 12.669% | 4.865% | 12.669% | 4.866% | constrained |
| VibeVoice streaming 7B, unpaced | Unpaced | 32.627% | 16.838% | 32.627% | 16.842% | constrained |
| VibeVoice streaming 1.5B, unpaced | Unpaced | 32.669% | 16.952% | 32.669% | 16.956% | constrained |
| VibeVoice streaming 1.5B, paced | Real-time paced | 32.947% | 17.210% | 32.947% | 17.215% | constrained |
| VibeVoice streaming 7B, paced | Real-time paced | 33.808% | 18.032% | 33.808% | 18.036% | constrained |

Unpaced = saved audio processed without waiting. Two-speaker correction uses the complete output after the stream, not a live speaker-count decision. These scores do not measure latency.

## Earlier selected settings and timings

The earlier best-tested settings are retained below as a separate record. They mix speaker constraints and decoding policies, so they are not the paired comparison above. Precision-2 only has a known-two API run here; it cannot supply an automatic/folded pair. The tuned Model X streaming decoder also changes thresholds and drops extra speakers rather than folding them. Its result is retained here, not relabelled as the common folding method.

### Batch / offline

Ordered by **common-interval DER at ±250 ms**, lowest first. Speaker policies still differ.

| System | Speaker policy | Whole DER, zero | Whole DER, ±250 ms | Common DER, zero | Common DER, ±250 ms | Whole-file count accuracy | Speed |
|---|---|---:|---:|---:|---:|---:|---|
| pyannoteAI Precision-2 API | Known 2 | 11.004% | 2.823% | 10.986% | 2.824% | constrained | 12 s/file, API round trip |
| Sortformer v1, 180 s windows, FP32 | Folded to 2 after inference | 12.706% | 3.159% | 12.706% | 3.159% | constrained | 1.7 s/file (274×), L4 batch |
| Sortformer v2.1, 30.4 s preset, FP32 | Folded to 2 after inference | 11.407% | 3.945% | 11.407% | 3.946% | constrained | 1.1 s/file (402×), L4 batch |
| Model X, 30.4 s preset, BF16 | Automatic | 12.593% | 4.786% | 12.593% | 4.787% | 80.0% | 0.7 s/file (768×), L4 batch |
| pyannoteAI Community-1, whole-file | Known 2; historical folding to 2 | 15.856% | 6.323% | 15.855% | 6.325% | constrained | 18.5 s/file (31×), L4 batch |
| VibeVoice-ASR, native batch | Automatic | 24.191% | 8.233% | 24.191% | 8.235% | 100.0% | 123 s/file, joint ASR+diarization server |
| Meta Muse Voice Transcribe | Automatic per request | 29.169%\* | 13.042%\* | 29.169% | 13.042% | 90.0%\* | 92 s/request, API round trip |

\* **Muse:** starred cells use the same **20 independently scored intervals** as its common-interval results, not whole-recording scores. Five recordings were split at the API's 10-minute limit; speaker-count accuracy is **18/20 intervals (90%)**. Speaker identity across chunk boundaries is not evaluated.

### Streaming diarization

Ordered by **common-interval DER at ±250 ms**, lowest first. Speaker policies still differ.

| System | Input pacing | Speaker policy | Whole DER, zero | Whole DER, ±250 ms | Common DER, zero | Common DER, ±250 ms | Whole-file count accuracy | Speed |
|---|---|---|---:|---:|---:|---:|---:|---|
| pyannoteAI live API | Real-time paced | Automatic | 10.515% | 3.959% | 10.515% | 3.960% | 66.7% | — |
| Model X, 1.04 s preset, unpaced, tuned decoding, FP32 | Unpaced | Tuned; top 2 speakers retained | 12.567% | 4.275% | 12.567% | 4.277% | constrained | 19.8 s/file (29×), L4 batch |
| Sortformer v2.1, 1.04 s preset, unpaced, FP32 | Unpaced | Folded to 2 after inference | 12.496% | 4.815% | 12.496% | 4.816% | constrained | 36.4 s/file (16×), L4 batch |
| VibeVoice streaming 7B, unpaced | Unpaced | Automatic | 32.627% | 16.838% | 32.627% | 16.842% | 93.3% | — |
| VibeVoice streaming 1.5B, unpaced | Unpaced | Automatic | 32.669% | 16.952% | 32.669% | 16.956% | 100.0% | — |
| VibeVoice streaming 1.5B, paced | Real-time paced | Automatic | 32.947% | 17.210% | 32.947% | 17.215% | 100.0% | — |
| VibeVoice streaming 7B, paced | Real-time paced | Automatic | 33.808% | 18.032% | 33.808% | 18.036% | 86.7% | — |

**Speed in this table:** unpaced replay of the chunk loop on one L4, batch size 1; it is throughput of the streaming preset on saved audio, not live latency.

**Input pacing:** real-time paced runs receive audio at normal speaking speed; unpaced runs process prerecorded audio without that timing constraint. DER measures diarization accuracy, not live latency. Speaker constraints remain specific to each row.

See [methodology](../docs/METHODOLOGY.md), [paired score counts](speaker_policy_snapshot.json), [settings log](best_settings_receipt.json), and [run instructions](../inference/README.md).
