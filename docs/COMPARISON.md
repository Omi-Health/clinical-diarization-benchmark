# How to compare the benchmark

## Main tables

Use automatic speaker counts and DER at ±250 ms for every headline row. That collar excludes 250 ms on either side of each reference boundary; it is a scoring convention, not an Omi runtime setting. Strict zero-tolerance DER remains in the full results because gap handling can improve one score while worsening the other.

The primary panel covers all 15 whole recordings. Muse was requested in 20 chunks and is therefore compared in the shared-interval table instead. The intervals match, but inference context and speaker continuity across chunks do not.

NVIDIA models were run locally on one L4 with the released Nemotron 3 checkpoint ([exact settings and reproduction](GA_20260924.md)); hosted APIs were measured through their public endpoints on the dates recorded in the full results. Known-two API calls, whole-file folding and tuned top-two selection are supplementary and live in the full configuration tables. They do not determine the automatic-count ranking.

## Model, runtime and service

| Layer | What is measured |
|---|---|
| Baseline | Model with its recorded native decoding, precision and inference settings |
| Omi runtime | Same weights with execution and segment-processing changes; code remains proprietary |
| Deployed service | API transport, queues, shared load and delivery, requiring separate qualification |

Omi rows are not claims about vanilla model performance or proof that the tested runtime is deployed. Same-weight comparisons can change precision and runtime settings together; they do not isolate individual optimizations. The optimized Community-1 rows and v1 windowed recipes are in the full results.

## Speaker policies

Automatic count accuracy is the fraction of whole recordings with the correct number of nonempty labels. It complements DER: two labels can still be assigned to the wrong turns, while an extra brief label can have a small DER penalty.

A native known-count parameter differs from custom folding. Our supplementary duration fold keeps the two longest-speaking labels and maps all extra labels into the second. It uses no reference mapping, but uses prior knowledge that the recording contains two speakers. It does not compare voices and cannot be called a native two-speaker mode. Windowed v1's raw count is affected by stitching; its whole-file baseline is used in the headline table.

## Streaming and speed

- Delivered rows are reconstructed from emitted events and revisions. Final reconstructed accuracy does not measure correctness at every instant before a revision.
- Native streaming-preset rows score completed replay output and are labelled retrospective.
- Real-time pacing and unpaced replay are different. Unpaced processing time measures throughput, not caller-facing update latency or concurrent-stream capacity.

L4 timings are local, one recording at a time. API timings include transport, service and polling; VibeVoice includes ASR as well as diarization. Do not rank them as pure hardware-speed measurements. Fresh GA timings exclude a same-process warmup; older runs retain their recorded warmup and software differences.

A future latency panel needs a common paced sender and explicit event semantics: first speaker, coverage lag, revisions, completion after Stop and failures. Do not convert unpaced speed into supported simultaneous streams.

## Limits and disclosure

This is a small set of simulated two-party consultations, with VAD-refined turn references rather than adjudicated speaker truth. Several runtime choices were developed on this cohort. It is not an eight-speaker benchmark, held-out clinical qualification or evidence that tiny score differences are statistically significant.

Saved baseline and Omi runtime outputs are public and rescored in CI. They contain speaker labels and timestamps only. Omi’s implementation remains private; score verification does not reproduce its inference.
