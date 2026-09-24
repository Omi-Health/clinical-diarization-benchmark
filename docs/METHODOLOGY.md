# Methodology

**Headline run:** [24 September 2026 protocol and results](GA_20260924.md) for the NVIDIA models on one L4. Main tables use automatic counts and ±250 ms DER; strict scores remain in the full results. The configuration descriptions and timings below cover every other row and the full configuration tables.


## Comparison layout

The [comparison rules](COMPARISON.md) distinguish public baseline, Omi runtime
and deployed service. Batch recipes are grouped by model and labelled by speaker
policy. Delivered realtime outputs are separate from retrospective streaming
replays. No scores or reference protocol changed for this presentation.

## Dataset and reference preparation

The snapshot uses 15 previously frozen recordings from PriMock57, a public dataset of simulated primary-care consultations. Every recording has a doctor and a patient. Case IDs, durations and frozen mixed-audio SHA-256 hashes are in `data/manifest.json`. Total duration is 8,694.664 seconds (2.415184 hours).

The audio preparation adds the synchronized doctor and patient PCM16 tracks in a wider integer type, clips the sum to the PCM16 range, and trims to the final text-bearing reference boundary. Input is 16 kHz mono. The exact 15 mixed WAVs are included under `data/raw_audio/` through Git LFS, under CC BY 4.0. Use `scripts/verify_audio.py` to verify the frozen hashes, formats and durations before a matched rerun. The WAVs contain only format and PCM audio chunks, with no additional metadata.

The frozen timing references intersect the source TextGrid speech turns with Silero VAD speech intervals on the mixed conversation. This removes some silence inside broad reference turns. The exported JSON retains only start/end times and speaker labels. Common-interval references are exported from the exact frozen split references used for the reported scores.

**Reference limitation:** VAD-refined timing can miss quiet speech, retain noise, or affect systems differently. It is not hand-adjudicated speech truth. These results are specific to this reference construction and should not be equated with scores against the original turn-level annotations. The exact frozen intervals are included so scoring does not depend on rerunning VAD with potentially different defaults.

This is a small, repeatedly used comparison subset, not a newly sealed holdout. The selected recordings have been evaluated repeatedly. No confidence intervals or statistical-significance claims are made; a close ordering here may not generalize. No multi-party board audio is in this snapshot.

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

The main panel uses one speaker permutation per complete recording. Muse's request limit required five recordings longer than 600 seconds to be split. It therefore has no whole-recording score here.

The common panel uses the same 20 intervals for every system: ten complete recordings and ten parts from the other five recordings. Each interval gets a separate permutation. Other systems' complete-recording outputs are clipped into these intervals; their inference is not rerun on the chunks.

This equalizes scoring support, **not inference context**. It does not evaluate speaker identity continuity across the split. Extra boundaries and frame rounding can slightly change both the denominator and score. Exact interval durations and offsets are in the manifest.

## Matched speaker policies

The controlled tables score the same saved automatic inference outputs twice: unchanged, then passed through `normalize_max_speakers(segments, 2)`. The function keeps the two labels with the most summed segment duration, relabels them and maps every extra label onto the second. It keeps all segment activity; it does not discard extra-speaker speech or force a missing second speaker to appear. It uses no reference labels or timings. For streaming rows this is retrospective post-processing of the completed output, not causal live correction. Whole-recording outputs are folded before clipping to common intervals; Muse is folded per request interval because no whole-recording output exists.

The NVIDIA pairs hold FP32 and the inference configuration fixed. Sortformer v1 uses 180 s windows and 12 s overlap; its automatic output includes errors from window stitching. Those automatic DER and count cells display "n/a (windowed)" rather than a model-only result; the numeric snapshot and settings log retain the raw scores and the whole-file variant. V2.1 and Nemotron 3 Diarization use native annotation decoding with their offline or 1.04 s presets. A tuned probability decoder is not used in these pairs. The public automatic presets are in `inference/configs/speaker-policies/`; both policies use `inference/speaker_policies.py`.

Community-1 uses its saved automatic-count L4 output for both policies. Precision-2 has only a known-two API run, so it is retained in the best-tested table, not inserted into a paired comparison. Other vendors use their saved automatic outputs.

`results/speaker_policy_snapshot.json` contains the paired integer counts. `scripts/verify_speaker_policies.py` recomputes all public pairs from their saved automatic outputs; `scripts/crosscheck_pyannote.py --speaker-policies` independently checks their whole-recording scores in continuous time.

## Best-tested inference policies

These are third-party model configurations evaluated by Omi. Omi runtime rows are listed separately below (see "Omi runtime rows").

The Sortformer configurations in the full tables were run with the public `inference/run.py` on one dedicated NVIDIA L4 (18 September 2026) in the pinned NeMo environment, batch size 1, complete recordings, at FP32 and BF16, with and without the two-speaker fold. Sortformer v1 is windowed (180 s, 12 s overlap) because whole-file inference on these 6–14 minute recordings is outside its 90-second training context and collapsed one 13-minute recording into file-wide label confusion; Sortformer v2.1 predicts three or four labels on most of these two-person recordings, so its folded rows use the known count of two. The 24 September L4 run scores the same models under automatic counts. Every setting tried is in the [settings log](../results/best_settings_receipt.json).

| System | Inference / output policy |
|---|---|
| Sortformer v1 | 180-second windows, 12-second overlap, FP32; folded to two speakers after inference |
| Sortformer v2.1 offline | 30.4-second buffer preset, FP32; folded to two speakers after inference |
| Sortformer v2.1 streaming | 1.04-second buffer preset, unpaced replay, FP32; folded to two speakers after inference |
| Nemotron 3 Diarization | Released checkpoint, pinned revision; offline 30.4-second preset and 1.04-second streaming preset, BF16, automatic speaker count; see the [L4 run record](GA_20260924.md) |
| pyannoteAI Community-1 | Known-two inference plus two-speaker normalization |
| pyannoteAI Precision-2 | Whole-file API with the known count of two |
| pyannoteAI Precision-3 | Whole-file API (`model: precision-3`), run 2026-09-21 twice: automatic speaker count, and the known count of two (`numSpeakers: 2`); the common-interval parts were cut from the frozen audio at the manifest offsets and diarized separately, as for Precision-2 |
| pyannoteAI live API | Real-time-paced requests; automatic labels |
| Meta Muse | Automatic labels per request; five recordings split at 600 seconds |
| VibeVoice-ASR | Native batch output; automatic labels |
| VibeVoice streaming 1.5B / 7B | Paced and separate unpaced runs; automatic labels |

The folded Sortformer rows and the known-two pyannote batch rows use the same speaker-count information; automatic-count rows do not, so the combined configuration table is not a fair single ranking. The headline tables use automatic counts throughout.

## Omi runtime rows

Omi rows use unchanged model weights with a proprietary runtime. Runtime choices were developed on these 15 recordings, not a held-out set. Execution and output handling can change together; no individual optimization is credited with the gains.

Automatic and constrained speaker policies remain explicit per row. Supplementary known-two and retrospective rows are not native automatic or causal live results. Headline Omi streaming scores use the revisions delivered during the stream.

Saved speaker/timestamp outputs are public for every model and Omi runtime variant, so all reported scores can be checked. Omi’s implementation, tuning details and raw live traces remain private.

Both strict and ±250 ms DER are reported, including cases where strict DER worsens. All measured configurations remain in the [settings log](../results/best_settings_receipt.json), identified without exposing proprietary settings. [Community-1 automatic timing](../results/community1_timing.json) includes all 15 per-recording totals for baseline and Omi.

### Speed

The speed column reports median wall time per recording; × real time is total audio duration divided by summed processing time, not the reciprocal of that median. L4 rows ran sequentially at batch size 1 on the same NVIDIA L4 (g6.2xlarge). Model loading is excluded. All 15 timed recordings are included.

Sortformer used the public runner (NeMo 3.1.0, PyTorch 2.8.0a0+34c6371d24.nv25.08), including audio loading, decoding/postprocessing and output writes. A separate one-recording process ran before each configuration; this can warm filesystem caches, but does not warm CUDA or the model in the measured process. Its first recording remains in the timing totals. Community-1 used pyannote.audio 4.0.7 with PyTorch 2.14.0+cu130 in a separate container; each known-two call followed an automatic-count call on the same file. Its pipeline timings include audio loading but exclude output serialization. Its accuracy reproduced the 2026-09-07 scores. These are observed run times, not a controlled steady-state speed ranking.

Streaming presets replay saved audio without pacing: their times measure throughput, not live latency. API times include upload, queueing and polling per request; Muse used 20 requests for 15 recordings, at concurrency 8. VibeVoice ran joint ASR plus diarization behind a larger vLLM server requiring about 30 GB of GPU memory, so its request time includes transcription and was not remeasured on the L4. Per-row values are in `results/best_settings_receipt.json`.

### Streaming interpretation

The included runner submits saved complete recordings to NeMo, whose streaming checkpoints process them with the selected chunk/cache geometry. It does not pace audio at speaking speed or measure incremental emission times. The two low-latency presets each buffer 1.04 seconds of chunk plus right context; this is a configuration value, not measured end-to-end latency. These rows remain labelled **unpaced**.

The pyannoteAI live run used 16 kHz mono float32 PCM, 100 ms chunks and wall-clock pacing at 1× audio speed. Its `/v1/live` endpoint did not expose a model selector. Provider speaker events were converted to intervals; open intervals at stream close were ended at the recording duration (10 intervals across 9 recordings). No speaker-count folding is applied.

For VibeVoice, the saved official segment timing is used, including coarse/chunk-derived boundaries. Explicitly unlabelled `[Silence]`, `[Noise]` or empty annotations produce no attributed speaker activity. Other unlabelled content fails the normalization instead of being silently discarded. Speaker-labelled non-speech and segments spanning pauses remain scored; there is no reference-based silence masking or timestamp repair.

Correct speaker count in a constrained run is not a measure of automatic counting ability. For automatic whole-recording runs, accuracy is the fraction of recordings whose number of distinct nonempty predicted speaker labels equals two.

## What is independently checkable

All named baseline rows include their normalized speaker/timestamp outputs, frozen references and per-case integer counts. `scripts/verify_snapshot.py` recomputes these scores and checks every exported data hash. The L4 run verifier also rescores every saved Omi runtime view from sanitized speaker/timestamp outputs.

The Sortformer and Nemotron 3 Diarization results come from GPU inference with the included code and presets; see [run instructions](../inference/README.md). Exact Sortformer checkpoint pins, the container image and NeMo source revision are public. Runtime receipts record code/configuration hashes and native outputs; Omi runtime raw receipts remain private. Vendor results are exported API outputs, and their inference clients are not bundled. Displayed names identify the evaluated versions, not necessarily the latest products.

The independent `scripts/crosscheck_pyannote.py` uses separate tracks for simultaneous speakers, unions overlapping hypothesis intervals for the same speaker, and scores the complete recording duration including silence. It compares the continuous-time scorer with the 10 ms scorer at both collars. Some small differences are expected from frame sampling and boundary placement.
No throughput leaderboard is provided. Bare diarization, joint ASR/diarization and remote APIs perform different work; hardware, network and timing scopes differ. These numbers are not evidence of streaming latency, clinical safety or transcription accuracy.
