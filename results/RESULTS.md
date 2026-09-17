# Diarization results

Snapshot: 2026-09-17. Same 15 PriMock mock consultations, 2.4152 audio hours.

DER ↓ is a percentage; lower is better. Speaker policies differ and are part of each result. These are historical system configurations, not a controlled model-only ranking.

## Batch / offline

Ordered by **common-interval DER at ±250 ms**, lowest first. Speaker policies still differ.

| System | Speaker policy | Whole DER, zero | Whole DER, ±250 ms | Common DER, zero | Common DER, ±250 ms | Whole-file count accuracy |
|---|---|---:|---:|---:|---:|---:|
| Precision-2 API | Known 2 | 11.004% | 2.823% | 10.986% | 2.824% | constrained |
| Sortformer v1, 180s windows | Folded to 2 after inference | 12.706% | 3.157% | 12.706% | 3.158% | constrained |
| Sortformer v2.1, whole-file | Folded to 2 after inference | 12.173% | 3.610% | 12.173% | 3.611% | constrained |
| Model X | Automatic | 12.589% | 4.786% | 12.589% | 4.787% | 80.0% |
| Community-1, whole-file | Known 2; historical folding to 2 | 15.856% | 6.323% | 15.855% | 6.325% | constrained |
| VibeVoice-ASR, native batch | Automatic | 24.191% | 8.233% | 24.191% | 8.235% | 100.0% |
| Meta Muse Voice Transcribe | Automatic per request | 29.169%\* | 13.042%\* | 29.169% | 13.042% | 90.0%\* |

\* **Muse:** starred cells use the same **20 independently scored intervals** as its common-interval results, not whole-recording scores. Five recordings were split at the API's 10-minute limit; speaker-count accuracy is **18/20 intervals (90%)**. Speaker identity across chunk boundaries is not evaluated.

## Real-time-paced streaming

Ordered by **common-interval DER at ±250 ms**, lowest first. Speaker policies still differ.

| System | Speaker policy | Whole DER, zero | Whole DER, ±250 ms | Common DER, zero | Common DER, ±250 ms | Whole-file count accuracy |
|---|---|---:|---:|---:|---:|---:|
| VibeVoice streaming 1.5B, paced | Automatic | 32.947% | 17.210% | 32.947% | 17.215% | 100.0% |
| VibeVoice streaming 7B, paced | Automatic | 33.808% | 18.032% | 33.808% | 18.036% | 86.7% |

## Supplementary: streaming checkpoints run unpaced

Ordered by **common-interval DER at ±250 ms**, lowest first. Speaker policies still differ.

| System | Speaker policy | Whole DER, zero | Whole DER, ±250 ms | Common DER, zero | Common DER, ±250 ms | Whole-file count accuracy |
|---|---|---:|---:|---:|---:|---:|
| VibeVoice streaming 7B, unpaced | Automatic | 32.627% | 16.838% | 32.627% | 16.842% | 93.3% |
| VibeVoice streaming 1.5B, unpaced | Automatic | 32.669% | 16.952% | 32.669% | 16.956% | 100.0% |

## Reading the results

- **Model X:** anonymized system. Aggregate results only; its inference code, configuration and individual outputs are private. The public repo cannot independently reproduce this row.
- **±250 ms** means a 250 ms exclusion radius around each reference boundary (pyannote total collar **0.5 seconds**). Zero collar is also shown. This is a 10 ms frame scorer, not a claim of bitwise parity with a continuous-time scorer.
- **Common intervals:** the same 20 scoring intervals for every system. Muse required five long recordings to be split at 600 seconds. Matching is independent in each interval. Inference context remains different, and cross-interval speaker continuity is not measured.
- **Known/folded to 2:** these rows use information that automatic-count rows do not. A correct count for a constrained run does not demonstrate automatic speaker counting.
- **References:** frozen VAD-corrected timing annotations derived from PriMock57. Overlap and false alarms during silence are included. These are not hand-verified word-level speech boundaries.
- VibeVoice uses its returned timing, including coarse/chunk-derived boundaries. Speaker-labelled pauses count as false alarms; no reference-based silence mask repairs the predictions.
- No speed ranking: these systems perform different work (diarization alone versus ASR plus diarization), on different hardware or remote APIs.

See [methodology](../docs/METHODOLOGY.md), [data attribution](../data/ATTRIBUTION.md), and [numeric snapshot](snapshot.json).
