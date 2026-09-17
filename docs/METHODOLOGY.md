# Methodology

## Dataset and reference preparation

The snapshot uses 15 previously frozen recordings from PriMock57, a public dataset of simulated primary-care consultations. Every recording has a doctor and a patient. Case IDs, durations and frozen mixed-audio SHA-256 hashes are in `data/manifest.json`. Total duration is 8,694.664 seconds (2.415184 hours).

The historical audio preparation adds the synchronized doctor and patient PCM16 tracks in a wider integer type, clips the sum to the PCM16 range, and trims to the final text-bearing reference boundary. Input is 16 kHz mono. The exact 15 mixed WAVs are included under `data/raw_audio/` through Git LFS, under CC BY 4.0. Use `scripts/verify_audio.py` to verify the frozen hashes, formats and durations before a matched rerun. The WAVs contain only format and PCM audio chunks, with no additional metadata.

The frozen timing references intersect the source TextGrid speech turns with Silero VAD speech intervals on the mixed conversation. This removes some silence inside broad reference turns. The exported JSON retains only start/end times and speaker labels. Common-interval references are exported from the exact frozen split references used for the reported scores.

**Reference limitation:** VAD-refined timing can miss quiet speech, retain noise, or affect systems differently. It is not hand-adjudicated speech truth. These results are specific to this reference construction and should not be equated with scores against the original turn-level annotations. The exact frozen intervals are included so scoring does not depend on rerunning VAD with potentially different defaults.

This is a small historical comparison subset, not a newly sealed holdout. The selected recordings have been evaluated repeatedly. No confidence intervals or statistical-significance claims are made; a close ordering here may not generalize. No multi-party board audio is in this snapshot.

## DER definition

Frames are sampled at `(index + 0.5) * 0.01` seconds for `int(duration / 0.01)` frames. A segment is active on `[start, end)`. Predictions outside the recording are clipped. Repeated/overlapping segments for the same speaker are a single speaker activity.

Speaker labels are aligned one-to-one using Hungarian assignment to maximize matched reference/hypothesis speaker frames. For each scored frame:

- Miss = `max(reference speaker count - hypothesis speaker count, 0)`.
- False alarm = `max(hypothesis speaker count - reference speaker count, 0)`.
- Confusion = `min(reference speaker count, hypothesis speaker count) - correctly matched active speakers`.

DER = `(miss + false alarm + confusion) / reference speaker frames`. Overlap contributes speaker time for each reference speaker. Hypothesis activity in silence remains a false alarm. DER can exceed 100%. Corpus scores divide summed error counts by summed reference speaker frames, rather than averaging recording percentages.

A recording with no scored reference speech has undefined DER (`null`) while retaining its false-alarm counts. These counts still enter corpus aggregation.

## Collar conventions

Two panels are reported: no collar and a **0.25-second exclusion radius around every reference segment boundary**. The latter corresponds to a **0.5-second total collar** in pyannote terminology. It is not the same as a pyannote `collar=0.25` setting.

This implementation is frame-based. The collar convention is described for comparison; no claim is made that discretized scores equal every continuous-time scorer exactly. Excluded frames affect all speakers, including overlap, at that time.

## Whole recordings versus common intervals

The main panel uses one speaker permutation per complete recording. Muse's historical request limit required five recordings longer than 600 seconds to be split. It therefore has no whole-recording score here.

The common panel uses the same 20 intervals for every system: ten complete recordings and ten parts from the other five recordings. Each interval gets a separate permutation. Other systems' complete-recording outputs are clipped into these intervals; their inference is not rerun on the chunks.

This equalizes scoring support, **not inference context**. It does not evaluate speaker identity continuity across the split. Extra boundaries and frame rounding can slightly change both the denominator and score. Exact interval durations and offsets are in the manifest.

## Historical system policies

These are third-party model configurations evaluated by Omi. The tables do not report Omi's proprietary runtime performance; a separate runtime evaluation is planned.

| System | Saved inference / output policy |
|---|---|
| Sortformer v1 | 180-second windows, 12-second overlap; historical two-speaker folding before scoring |
| Sortformer v2.1 | Whole-file path; historical two-speaker folding before scoring |
| pyannoteAI Community-1 | Known two speakers during inference, plus historical two-speaker normalization |
| pyannoteAI Precision-2 | Whole-file API with the known count of two |
| pyannoteAI live API | Real-time-paced WebSocket requests, 100 ms PCM chunks, automatic labels |
| Sortformer v2.1, 1.04 s preset | Archived low-latency preset evaluated via whole-recording requests; historical two-speaker folding; supplementary unpaced results |
| Meta Muse | Automatic labels per request; five recordings split at 600 seconds |
| VibeVoice-ASR | Native batch output; automatic speaker labels |
| VibeVoice streaming 1.5B / 7B | Paced runs and separate supplemental unpaced runs; automatic labels |
| Model X | Automatic labels; aggregate-only disclosure |

Historical folding sorts labels by total segment duration, retains the two longest, and assigns any remaining label to the second retained label. It is an explicit limitation of these archived baselines. The included normalized outputs already incorporate it. The public scorer never silently applies folding or a speaker cap.

### Archived streaming runs

The pyannoteAI live run covers the same 15 audio hashes. Its recorded requests used 16 kHz mono float32 PCM, fixed 100 ms chunks and wall-clock pacing at 1× audio speed. The historical `/v1/live` endpoint did not expose a model selector, so this is labelled **pyannoteAI live API**, not Precision-2 streaming or a retroactively assigned model version. Speaker start/end events were converted to intervals using the provider's timestamps. At stream close, any still-open speaker interval was closed at the recording duration; this occurred for 10 intervals across 9 recordings. No other anomalies were recorded. No speaker-count folding is applied to the published live row; the correct count was returned on 10/15 recordings.

The additional Sortformer v2.1 run uses the archived 1.04-second streaming preset and the same 15 audio hashes. Its harness submitted each complete WAV in a file request, with a 3,600-second outer window covering every recording. It did not pace input at speaking speed. This evaluates the streaming preset's segmentation through prerecorded replay; it is not a paced live-client latency test. The historical max-two normalization remains explicit. This row is separate from later tune-selected postprocessors and from Omi's proprietary runtime.

Both added rows were rescored against the exact public frozen references at both collars. All whole-recording integer counts match their saved corrected-reference score files. Their common-interval scores were calculated by clipping predictions to the same published intervals. No inference was rerun to add these rows. No private server identifiers, event logs, access details or runtime code are included.

For VibeVoice, the saved official segment timing is used, including coarse/chunk-derived boundaries. Explicitly unlabelled `[Silence]`, `[Noise]` or empty annotations produce no attributed speaker activity. Other unlabelled content fails the historical normalization instead of being silently discarded. Speaker-labelled non-speech and segments spanning pauses remain scored; there is no reference-based silence masking or timestamp repair.

Correct speaker count in a constrained run is not a measure of automatic counting ability. For automatic whole-recording runs, accuracy is the fraction of recordings whose number of distinct nonempty predicted speaker labels equals two.

## What is independently checkable

All named baseline rows include their normalized speaker/timestamp outputs, frozen references and per-case integer counts. `scripts/verify_snapshot.py` recomputes these scores and checks every exported data hash. Model X exposes aggregate counts and percentages only; its arithmetic is checkable, but its predictions and inference are private.

Inference has not been rerun for this public release. This repository does not bundle the historical model runners or an end-to-end inference environment for the named baselines. Checkpoint revisions and full inference settings are not uniformly captured in the public snapshot. The displayed names identify the historical runs; they are not assertions about the latest versions of those products.

No throughput leaderboard is provided. Bare diarization, joint ASR/diarization and remote APIs perform different work; hardware, network and timing scopes differ. These numbers are not evidence of streaming latency, clinical safety or transcription accuracy.
