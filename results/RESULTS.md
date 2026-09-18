# Diarization results

Snapshot: 2026-09-18. Same 15 PriMock mock consultations, 2.4152 audio hours.

**Omi's proprietary runtime performance is not included.** These are third-party model configurations evaluated by Omi; our own runtime will be evaluated separately.

DER ↓ is a percentage; lower is better. Speaker policies differ and are part of each result. Sortformer and Model X were rerun natively on one L4; other rows retain their recorded vendor settings.

## Batch / offline

Ordered by **common-interval DER at ±250 ms**, lowest first. Speaker policies still differ.

| System | Speaker policy | Whole DER, zero | Whole DER, ±250 ms | Common DER, zero | Common DER, ±250 ms | Whole-file count accuracy |
|---|---|---:|---:|---:|---:|---:|
| pyannoteAI Precision-2 API | Known 2 | 11.004% | 2.823% | 10.986% | 2.824% | constrained |
| Model X, native offline | Automatic | 12.593% | 4.786% | 12.593% | 4.787% | 80.0% |
| pyannoteAI Community-1, whole-file | Known 2; historical folding to 2 | 15.856% | 6.323% | 15.855% | 6.325% | constrained |
| Sortformer v2.1, native offline | Automatic | 14.077% | 6.593% | 14.046% | 6.572% | 6.7% |
| Sortformer v1, native whole-file | Automatic | 14.784% | 6.778% | 14.784% | 6.630% | 93.3% |
| VibeVoice-ASR, native batch | Automatic | 24.191% | 8.233% | 24.191% | 8.235% | 100.0% |
| Meta Muse Voice Transcribe | Automatic per request | 29.169%\* | 13.042%\* | 29.169% | 13.042% | 90.0%\* |

\* **Muse:** starred cells use the same **20 independently scored intervals** as its common-interval results, not whole-recording scores. Five recordings were split at the API's 10-minute limit; speaker-count accuracy is **18/20 intervals (90%)**. Speaker identity across chunk boundaries is not evaluated.

## Streaming diarization

Ordered by **common-interval DER at ±250 ms**, lowest first. Speaker policies still differ.

| System | Input pacing | Speaker policy | Whole DER, zero | Whole DER, ±250 ms | Common DER, zero | Common DER, ±250 ms | Whole-file count accuracy |
|---|---|---|---:|---:|---:|---:|---:|
| pyannoteAI live API | Real-time paced | Automatic | 10.515% | 3.959% | 10.515% | 3.960% | 66.7% |
| Model X, native 1.04 s preset | Unpaced | Automatic | 12.746% | 4.962% | 12.746% | 4.963% | 60.0% |
| Sortformer v2.1, native 1.04 s preset | Unpaced | Automatic | 15.649% | 7.956% | 15.649% | 7.958% | 0.0% |
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
