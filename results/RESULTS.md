# Diarization results

Snapshot: 2026-09-18. Same 15 PriMock mock consultations, 2.4152 audio hours.

**Omi's proprietary runtime performance is not included.** These are third-party model configurations evaluated by Omi; our own runtime will be evaluated separately.

DER ↓ is a percentage; lower is better. Speaker policies differ and are part of each result. Each Sortformer/Model X row is shown at its best measured setting on this material; every other setting tried is logged with its score in `results/best_settings_receipt.json`. Other rows retain their recorded vendor settings.

## Batch / offline

Ordered by **common-interval DER at ±250 ms**, lowest first. Speaker policies still differ.

| System | Speaker policy | Whole DER, zero | Whole DER, ±250 ms | Common DER, zero | Common DER, ±250 ms | Whole-file count accuracy |
|---|---|---:|---:|---:|---:|---:|
| pyannoteAI Precision-2 API | Known 2 | 11.004% | 2.823% | 10.986% | 2.824% | constrained |
| Sortformer v1, 180 s windows, FP32 | Folded to 2 after inference | 12.706% | 3.159% | 12.706% | 3.159% | constrained |
| Sortformer v2.1, 30.4 s preset, FP32 | Folded to 2 after inference | 11.407% | 3.945% | 11.407% | 3.946% | constrained |
| Model X, 30.4 s preset, BF16 | Automatic | 12.593% | 4.786% | 12.593% | 4.787% | 80.0% |
| pyannoteAI Community-1, whole-file | Known 2; historical folding to 2 | 15.856% | 6.323% | 15.855% | 6.325% | constrained |
| VibeVoice-ASR, native batch | Automatic | 24.191% | 8.233% | 24.191% | 8.235% | 100.0% |
| Meta Muse Voice Transcribe | Automatic per request | 29.169%\* | 13.042%\* | 29.169% | 13.042% | 90.0%\* |

\* **Muse:** starred cells use the same **20 independently scored intervals** as its common-interval results, not whole-recording scores. Five recordings were split at the API's 10-minute limit; speaker-count accuracy is **18/20 intervals (90%)**. Speaker identity across chunk boundaries is not evaluated.

## Streaming diarization

Ordered by **common-interval DER at ±250 ms**, lowest first. Speaker policies still differ.

| System | Input pacing | Speaker policy | Whole DER, zero | Whole DER, ±250 ms | Common DER, zero | Common DER, ±250 ms | Whole-file count accuracy |
|---|---|---|---:|---:|---:|---:|---:|
| pyannoteAI live API | Real-time paced | Automatic | 10.515% | 3.959% | 10.515% | 3.960% | 66.7% |
| Model X, streaming preset, unpaced (tuned) | Unpaced | Tuned; top 2 speakers retained | 12.566% | 4.271% | 12.566% | 4.272% | constrained |
| Sortformer v2.1, 1.04 s preset, unpaced, FP32 | Unpaced | Folded to 2 after inference | 12.496% | 4.815% | 12.496% | 4.816% | constrained |
| VibeVoice streaming 7B, unpaced | Unpaced | Automatic | 32.627% | 16.838% | 32.627% | 16.842% | 93.3% |
| VibeVoice streaming 1.5B, unpaced | Unpaced | Automatic | 32.669% | 16.952% | 32.669% | 16.956% | 100.0% |
| VibeVoice streaming 1.5B, paced | Real-time paced | Automatic | 32.947% | 17.210% | 32.947% | 17.215% | 100.0% |
| VibeVoice streaming 7B, paced | Real-time paced | Automatic | 33.808% | 18.032% | 33.808% | 18.036% | 86.7% |

**Input pacing:** real-time paced runs receive audio at normal speaking speed; unpaced runs process prerecorded audio without that timing constraint. DER measures diarization accuracy, not live latency. Speaker constraints remain specific to each row.

## Reading the results

- **Model X:** anonymized system. Aggregate results only; inference code and presets are included. Replace the placeholder model name to run; individual outputs remain private. New runs can be compared with the published aggregates.
- **±250 ms** means a 250 ms exclusion radius around each reference boundary (pyannote total collar **0.5 seconds**). Zero collar is also shown. This is a 10 ms frame scorer, not a claim of bitwise parity with a continuous-time scorer.
- **Common intervals:** the same 20 scoring intervals for every system. Muse required five long recordings to be split at 600 seconds. Matching is independent in each interval. Inference context remains different, and cross-interval speaker continuity is not measured.
- **Known/folded to 2:** these rows use information that automatic-count rows do not. A correct count for a constrained run does not demonstrate automatic speaker counting.
- **References:** frozen VAD-corrected timing annotations derived from PriMock57. Overlap and false alarms during silence are included. These are not hand-verified word-level speech boundaries.
- VibeVoice uses its returned timing, including coarse/chunk-derived boundaries. Speaker-labelled pauses count as false alarms; no reference-based silence mask repairs the predictions.
- No speed ranking: these systems perform different work (diarization alone versus ASR plus diarization), on different hardware or remote APIs.

See [methodology](../docs/METHODOLOGY.md), [data attribution](../data/ATTRIBUTION.md), and [numeric snapshot](snapshot.json).
