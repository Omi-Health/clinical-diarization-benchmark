# Diarization results

**Dataset:** 15 mock consultations, 2.4152 audio hours · **Published:** September 2026

**DER ↓** = diarization error, with ±250 ms excluded around reference boundaries. Main tables use automatic speaker counts. Full results retain zero-tolerance scores and constrained experiments.

NVIDIA baselines use their pinned released checkpoints on one L4. Hosted APIs use their public endpoints. Dates and hardware are in the [measurement record](#measurement-record). [Run and reproduction details](../docs/GA_20260924.md).
## Batch: automatic speaker counts

Same 15 whole recordings. No supplied speaker count or forced two-speaker reassignment. NVIDIA models ran locally on one L4; hosted APIs were measured through their public endpoints.

| Model | DER ↓ (±250 ms) | Correct speaker count ↑ | Measured time ↓ |
|---|---:|---:|---|
| Pyannote Precision-3 API | 2.891% | 14/15 | 18.9 s/file · API round trip |
| Nemotron 3 Diarization | 4.803% | 14/15 | 0.688 s/file · L4 |
| Pyannote Community-1 | 6.620% | 9/15 | 18.691 s/file · L4 |
| Sortformer v1, whole-file BF16 | 6.778% | 14/15 | 3.869 s/file · L4 |
| Sortformer v2.1, FP32 | 7.974% | 3/15 | 1.077 s/file · L4 |
| VibeVoice-ASR | 8.233% | 15/15 | 123 s/file · joint ASR + diarization server |

Local L4 processing and hosted API round trips have different timing scopes. Standalone model results do not represent Omi’s production service. Muse was tested in separate chunks: its result is in the shared-interval table in the full results. Precision-2 known-two and windowed/folded Sortformer runs are in the full configuration tables. Measurement dates per row are in the [measurement record](#measurement-record).

## Batch: Omi runtime, automatic speaker counts

| Model | Baseline → Omi DER (±250 ms) | Change | Correct counts, before → after | Seconds/file, before → after | Speedup |
|---|---:|---:|---:|---:|---:|
| Nemotron 3 Diarization | 4.803% → 3.174% | -1.629 pp | 14/15 → 14/15 | 0.688 → 0.324 | 2.13× |
| Sortformer v2.1 | 7.974% → 7.487% | -0.487 pp | 3/15 → 3/15 | 1.077 → 0.854 | 1.26× |
| Pyannote Community-1 | 6.620% → 5.435% | -1.186 pp | 9/15 → 14/15 | 18.691 → 0.778 | 24.02× |

Same weights, no retraining. Saved speaker/timestamp outputs are public for every row; Omi’s runtime implementation stays private. Strict DER can worsen while collared DER improves; both scores remain in the full results.

## Streaming: automatic speaker counts

| Model / configuration | Output | DER ↓ (±250 ms) | Correct speaker count ↑ | Measured time ↓ |
|---|---|---:|---:|---|
| Pyannote live API | Delivered · paced | 3.959% | 10/15 | Latency not measured |
| Nemotron 3 Diarization + Omi | Delivered · unpaced | 4.575% | 14/15 | 7.540 s/file · L4 |
| Sortformer v2.1 + Omi | Delivered · unpaced | 6.458% | 5/15 | 38.549 s/file · L4 |
| VibeVoice 1.5B | Delivered · paced | 17.210% | 15/15 | Latency not measured |
| VibeVoice 7B | Delivered · paced | 18.032% | 13/15 | Latency not measured |
| Nemotron 3 Diarization, native preset | Retrospective · unpaced | 4.971% | 12/15 | 21.108 s/file · L4 |
| Sortformer v2.1, native preset | Retrospective · unpaced | 6.958% | 0/15 | 36.303 s/file · L4 |

Unpaced seconds/file measure processing throughput, not user-facing latency or concurrent-stream capacity. Native presets score the completed-file timeline; Omi live rows reconstruct delivered revisions. Sortformer v1 is offline-only.

## Shared intervals, including Muse

The same 20 intervals cover all 15 sources. Whole-file systems retain full-file context; Muse used separate requests. Correct counts below refer to intervals, not whole recordings.

| Model | DER ↓ (±250 ms) | Correct interval counts | Measured time |
|---|---:|---:|---|
| Pyannote Precision-3 API | 2.895% | 19/20 | 18.9 s/file · API round trip |
| Nemotron 3 Diarization | 4.804% | 19/20 | 0.688 s/file · L4 |
| Pyannote Community-1 | 6.622% | 13/20 | 18.691 s/file · L4 |
| Sortformer v1, whole-file BF16 | 6.630% | 19/20 | 3.869 s/file · L4 |
| Sortformer v2.1, FP32 | 6.832% | 4/20 | 1.077 s/file · L4 |
| VibeVoice-ASR | 8.235% | 20/20 | 123 s/file · joint ASR + diarization server |
| Meta Muse Voice Transcribe | 13.042% | 18/20 | 92 s/request · API round trip |

## Nemotron 3 and Sortformer L4 run: full scoring details

Every tested view is retained. `known2` forces at most two labels after inference; `top2` drops extra channels. Those are supplementary processing experiments, not automatic model results. Windowed v1 count errors include stitching artifacts. All saved outputs can be rescored; Omi’s implementation remains private.

| Run | Output view | Whole DER zero | Whole DER ±250 ms | Common DER zero | Common DER ±250 ms | Whole count accuracy |
|---|---|---:|---:|---:|---:|---:|
| ga_live_graph | delivered_causal | 13.093% | 4.575% | 13.093% | 4.576% | 14/15 |
| ga_off_bf16 | native | 12.720% | 4.803% | 12.720% | 4.804% | 14/15 |
| ga_off_bf16 | native_known2 | 12.720% | 4.803% | 12.720% | 4.804% | constrained |
| ga_off_bf16 | model_card | 12.720% | 4.803% | 12.720% | 4.804% | 14/15 |
| ga_off_bf16 | model_card_known2 | 12.720% | 4.803% | 12.720% | 4.804% | constrained |
| ga_off_bf16 | omi_automatic | 13.209% | 3.176% | 13.209% | 3.177% | 14/15 |
| ga_off_bf16 | omi_automatic_known2 | 13.209% | 3.176% | 13.209% | 3.177% | constrained |
| ga_off_bf16 | native_merge | 13.287% | 3.289% | 13.287% | 3.290% | 14/15 |
| ga_off_bf16 | native_merge_known2 | 13.287% | 3.289% | 13.287% | 3.290% | constrained |
| ga_off_bf16 | tuned_top2_merge | 13.206% | 3.176% | 13.206% | 3.177% | constrained |
| ga_off_fp32 | native | 12.718% | 4.795% | 12.718% | 4.796% | 14/15 |
| ga_off_fp32 | native_known2 | 12.718% | 4.795% | 12.718% | 4.796% | constrained |
| ga_off_fp32 | model_card | 12.718% | 4.795% | 12.718% | 4.796% | 14/15 |
| ga_off_fp32 | model_card_known2 | 12.718% | 4.795% | 12.718% | 4.796% | constrained |
| ga_off_fp32 | omi_automatic | 13.203% | 3.174% | 13.203% | 3.175% | 14/15 |
| ga_off_fp32 | omi_automatic_known2 | 13.203% | 3.174% | 13.203% | 3.175% | constrained |
| ga_off_fp32 | native_merge | 13.304% | 3.308% | 13.304% | 3.309% | 14/15 |
| ga_off_fp32 | native_merge_known2 | 13.304% | 3.308% | 13.304% | 3.309% | constrained |
| ga_off_fp32 | tuned_top2_merge | 13.200% | 3.174% | 13.200% | 3.175% | constrained |
| ga_omi_graph | native | 12.709% | 4.788% | 12.709% | 4.789% | 14/15 |
| ga_omi_graph | native_known2 | 12.709% | 4.788% | 12.709% | 4.789% | constrained |
| ga_omi_graph | model_card | 12.709% | 4.788% | 12.709% | 4.789% | 14/15 |
| ga_omi_graph | model_card_known2 | 12.709% | 4.788% | 12.709% | 4.789% | constrained |
| ga_omi_graph | omi_automatic | 13.203% | 3.174% | 13.203% | 3.175% | 14/15 |
| ga_omi_graph | omi_automatic_known2 | 13.203% | 3.174% | 13.203% | 3.175% | constrained |
| ga_omi_graph | native_merge | 13.302% | 3.300% | 13.302% | 3.301% | 14/15 |
| ga_omi_graph | native_merge_known2 | 13.302% | 3.300% | 13.302% | 3.301% | constrained |
| ga_omi_graph | tuned_top2_merge | 13.200% | 3.174% | 13.200% | 3.175% | constrained |
| ga_stream_bf16 | native | 12.921% | 4.971% | 12.921% | 4.972% | 12/15 |
| ga_stream_bf16 | native_known2 | 12.867% | 4.907% | 12.867% | 4.908% | constrained |
| ga_stream_bf16 | model_card | 12.921% | 4.971% | 12.921% | 4.972% | 12/15 |
| ga_stream_bf16 | model_card_known2 | 12.867% | 4.907% | 12.867% | 4.908% | constrained |
| ga_stream_bf16 | omi_automatic | 13.354% | 3.321% | 13.354% | 3.322% | 12/15 |
| ga_stream_bf16 | omi_automatic_known2 | 13.299% | 3.254% | 13.299% | 3.255% | constrained |
| ga_stream_bf16 | native_merge | 13.410% | 3.429% | 13.410% | 3.430% | 12/15 |
| ga_stream_bf16 | native_merge_known2 | 13.356% | 3.365% | 13.356% | 3.366% | constrained |
| ga_stream_bf16 | tuned_top2_merge | 13.354% | 3.321% | 13.354% | 3.322% | constrained |
| v1_omi_tf32 | native | 18.555% | 9.474% | 15.921% | 6.602% | window stitching |
| v1_omi_tf32 | native_known2 | 12.706% | 3.159% | 12.706% | 3.159% | constrained |
| v1_omi_tf32 | omi_merge | 19.387% | 9.491% | 16.743% | 6.610% | window stitching |
| v1_omi_tf32 | omi_merge_known2 | 13.518% | 3.159% | 13.518% | 3.160% | constrained |
| v1_whole_bf16 | native | 14.784% | 6.778% | 14.784% | 6.630% | 14/15 |
| v1_whole_bf16 | native_known2 | 14.122% | 6.143% | 14.122% | 5.994% | constrained |
| v1_whole_bf16 | model_card | 14.784% | 6.778% | 14.784% | 6.630% | 14/15 |
| v1_whole_bf16 | model_card_known2 | 14.122% | 6.143% | 14.122% | 5.994% | constrained |
| v1_whole_bf16 | omi_automatic | 16.714% | 6.701% | 16.714% | 6.536% | 14/15 |
| v1_whole_bf16 | omi_automatic_known2 | 16.047% | 6.055% | 16.047% | 5.890% | constrained |
| v1_whole_bf16 | native_merge | 16.303% | 6.398% | 16.303% | 6.165% | 14/15 |
| v1_whole_bf16 | native_merge_known2 | 15.622% | 5.750% | 15.622% | 5.517% | constrained |
| v1_whole_bf16 | tuned_top2_merge | 16.668% | 6.701% | 16.668% | 6.536% | constrained |
| v1_win_fp32 | native | 18.556% | 9.474% | 15.921% | 6.602% | window stitching |
| v1_win_fp32 | native_known2 | 12.705% | 3.157% | 12.705% | 3.158% | constrained |
| v1_win_fp32 | omi_merge | 19.388% | 9.491% | 16.743% | 6.610% | window stitching |
| v1_win_fp32 | omi_merge_known2 | 13.517% | 3.158% | 13.517% | 3.158% | constrained |
| v21_live_tf32 | delivered_causal | 15.501% | 6.458% | 15.501% | 6.460% | 5/15 |
| v21_off_fp32 | native | 15.768% | 7.974% | 14.543% | 6.832% | 3/15 |
| v21_off_fp32 | native_known2 | 11.407% | 3.945% | 11.407% | 3.946% | constrained |
| v21_off_fp32 | model_card | 15.768% | 7.974% | 14.543% | 6.832% | 3/15 |
| v21_off_fp32 | model_card_known2 | 11.407% | 3.945% | 11.407% | 3.946% | constrained |
| v21_off_fp32 | omi_automatic | 18.448% | 7.639% | 17.196% | 6.474% | 3/15 |
| v21_off_fp32 | omi_automatic_known2 | 14.135% | 3.655% | 14.135% | 3.656% | constrained |
| v21_off_fp32 | native_merge | 18.391% | 7.618% | 17.152% | 6.496% | 3/15 |
| v21_off_fp32 | native_merge_known2 | 13.953% | 3.551% | 13.953% | 3.552% | constrained |
| v21_off_fp32 | tuned_top2_merge | 17.984% | 7.767% | 17.984% | 7.769% | constrained |
| v21_omi_tf32 | native | 15.566% | 7.790% | 14.358% | 6.599% | 3/15 |
| v21_omi_tf32 | native_known2 | 11.370% | 3.907% | 11.370% | 3.908% | constrained |
| v21_omi_tf32 | model_card | 15.566% | 7.790% | 14.358% | 6.599% | 3/15 |
| v21_omi_tf32 | model_card_known2 | 11.370% | 3.907% | 11.370% | 3.908% | constrained |
| v21_omi_tf32 | omi_automatic | 18.261% | 7.487% | 17.048% | 6.291% | 3/15 |
| v21_omi_tf32 | omi_automatic_known2 | 14.109% | 3.642% | 14.109% | 3.642% | constrained |
| v21_omi_tf32 | native_merge | 18.186% | 7.436% | 16.962% | 6.248% | 3/15 |
| v21_omi_tf32 | native_merge_known2 | 13.924% | 3.518% | 13.924% | 3.519% | constrained |
| v21_omi_tf32 | tuned_top2_merge | 17.757% | 7.552% | 17.757% | 7.554% | constrained |
| v21_stream_fp32 | native | 14.841% | 6.958% | 14.841% | 6.960% | 0/15 |
| v21_stream_fp32 | native_known2 | 12.496% | 4.815% | 12.496% | 4.816% | constrained |
| v21_stream_fp32 | model_card | 14.841% | 6.958% | 14.841% | 6.960% | 0/15 |
| v21_stream_fp32 | model_card_known2 | 12.496% | 4.815% | 12.496% | 4.816% | constrained |
| v21_stream_fp32 | omi_automatic | 17.422% | 6.588% | 17.422% | 6.590% | 0/15 |
| v21_stream_fp32 | omi_automatic_known2 | 15.316% | 4.670% | 15.316% | 4.672% | constrained |
| v21_stream_fp32 | native_merge | 17.448% | 6.692% | 17.448% | 6.694% | 0/15 |
| v21_stream_fp32 | native_merge_known2 | 15.049% | 4.500% | 15.049% | 4.502% | constrained |
| v21_stream_fp32 | tuned_top2_merge | 16.934% | 6.294% | 16.934% | 6.296% | constrained |

## Additional fixed two-speaker recipes

These use complete-file speaker durations. They are not native known-speaker parameters or causal live results. All alternatives are in [the L4 run snapshot](ga-20260924/snapshot.json).

| Run | Processing order | DER ±250 ms |
|---|---|---:|
| ga_off_bf16 | duration_fold | 3.176% |
| ga_off_fp32 | duration_fold | 3.174% |
| ga_omi_graph | duration_fold | 3.174% |
| ga_stream_bf16 | duration_fold | 3.254% |
| v1_whole_bf16 | duration_fold | 6.055% |
| v21_off_fp32 | duration_fold | 3.631% |
| v21_omi_tf32 | duration_fold | 3.625% |
| v21_stream_fp32 | duration_fold | 4.612% |
| ga_off_bf16 | fold_then_merge | 3.289% |
| ga_off_fp32 | fold_then_merge | 3.308% |
| ga_omi_graph | fold_then_merge | 3.300% |
| ga_stream_bf16 | fold_then_merge | 3.365% |
| v1_omi_tf32 | fold_then_merge | 3.159% |
| v1_whole_bf16 | fold_then_merge | 5.750% |
| v1_win_fp32 | fold_then_merge | 3.158% |
| v21_off_fp32 | fold_then_merge | 3.533% |
| v21_omi_tf32 | fold_then_merge | 3.500% |
| v21_stream_fp32 | fold_then_merge | 4.484% |

## Measurement record

Every row is a measurement made on the date shown; rows are not re-measured when others are added.

| Rows | Measured | Where |
|---|---|---|
| Nemotron 3 Diarization, Sortformer v1 and v2.1 (headline rows, Omi runtime rows, streaming presets) | 24 September 2026 | one NVIDIA L4 (g6.2xlarge, Frankfurt), released Nemotron 3 checkpoint pinned by revision and SHA-256 |
| Sortformer configuration study (FP32/BF16, folded and automatic) | 18 September 2026 | one NVIDIA L4, public `inference/run.py` |
| Pyannote Precision-3 API (automatic and known-two) | 21 September 2026 | hosted API, sequential requests |
| Pyannote Precision-2 API (known-two) | 29 August 2026 | hosted API, sequential requests |
| Pyannote Community-1 (automatic baseline and Omi runtime) | 21–22 September 2026 | NVIDIA L4; per-file timing in community1_timing.json |
| Pyannote Community-1 (known-two baseline) | 7 September 2026 (accuracy), 18 September 2026 (timing) | NVIDIA L4, Pyannote.audio 4.0.7 |
| Sortformer v2.1 supplementary Omi known-two batch | 7 September 2026 | production L4 measurement |
| Sortformer Omi supplementary windowed/retrospective recipes | 22 September 2026 | NVIDIA L4 |
| Meta Muse Voice Transcribe | 15 September 2026 | hosted API, 20 requests |
| VibeVoice-ASR (batch) | 15 September 2026 | local vLLM server, joint ASR + diarization |
| Pyannote live API; VibeVoice streaming 1.5B and 7B (paced and unpaced) | before 17 September 2026 | outputs frozen when the repository was first published; exact run dates were not recorded |

## Matched speaker-policy comparison

Each pair uses the same saved automatic output, unchanged or folded to at most two speakers with the same function. This isolates speaker-policy effects; it is not a native-versus-Omi runtime experiment. Streaming correction is retrospective.

### Batch / offline

#### Automatic speaker count

| System | Whole DER, zero | Whole DER, ±250 ms | Common DER, zero | Common DER, ±250 ms | Count accuracy |
|---|---:|---:|---:|---:|---:|
| Pyannote Community-1, automatic inference | 16.243% | 6.620% | 16.242% | 6.622% | 60.0% |
| Sortformer v2.1, 30.4 s preset, FP32 | 15.768% | 7.974% | 14.543% | 6.832% | 20.0% |
| VibeVoice-ASR, native batch | 24.191% | 8.233% | 24.191% | 8.235% | 100.0% |
| Meta Muse Voice Transcribe | 29.169%\* | 13.042%\* | 29.169% | 13.042% | 90.0%\* |
| Sortformer v1, 180 s windows, FP32 | n/a (windowed) | n/a (windowed) | n/a (windowed) | n/a (windowed) | n/a (windowed) |

#### Same two-speaker post-processing

| System | Whole DER, zero | Whole DER, ±250 ms | Common DER, zero | Common DER, ±250 ms | Count accuracy |
|---|---:|---:|---:|---:|---:|
| Sortformer v1, 180 s windows, FP32 | 12.706% | 3.159% | 12.706% | 3.159% | constrained |
| Sortformer v2.1, 30.4 s preset, FP32 | 11.407% | 3.945% | 11.407% | 3.946% | constrained |
| Pyannote Community-1, automatic inference | 16.089% | 6.574% | 16.087% | 6.575% | constrained |
| VibeVoice-ASR, native batch | 24.191% | 8.233% | 24.191% | 8.235% | constrained |
| Meta Muse Voice Transcribe | 29.157%\* | 13.042%\* | 29.157% | 13.042% | constrained |

\* Muse: 20 separate request intervals, not whole recordings. V1 automatic results are n/a: window stitching adds labels, so this is not a model-only counting result. Raw scores and the whole-file variant remain in the settings log.

### Streaming diarization

#### Automatic speaker count

| System | Input pacing | Whole DER, zero | Whole DER, ±250 ms | Common DER, zero | Common DER, ±250 ms | Count accuracy |
|---|---|---:|---:|---:|---:|---:|
| Pyannote live API | Real-time paced | 10.515% | 3.959% | 10.515% | 3.960% | 66.7% |
| Sortformer v2.1, 1.04 s preset, unpaced, FP32 | Unpaced | 14.841% | 6.958% | 14.841% | 6.960% | 0.0% |
| VibeVoice streaming 7B, unpaced | Unpaced | 32.627% | 16.838% | 32.627% | 16.842% | 93.3% |
| VibeVoice streaming 1.5B, unpaced | Unpaced | 32.669% | 16.952% | 32.669% | 16.956% | 100.0% |
| VibeVoice streaming 1.5B, paced | Real-time paced | 32.947% | 17.210% | 32.947% | 17.215% | 100.0% |
| VibeVoice streaming 7B, paced | Real-time paced | 33.808% | 18.032% | 33.808% | 18.036% | 86.7% |

#### Same two-speaker post-processing

| System | Input pacing | Whole DER, zero | Whole DER, ±250 ms | Common DER, zero | Common DER, ±250 ms | Count accuracy |
|---|---|---:|---:|---:|---:|---:|
| Pyannote live API | Real-time paced | 10.092% | 3.592% | 10.092% | 3.593% | constrained |
| Sortformer v2.1, 1.04 s preset, unpaced, FP32 | Unpaced | 12.496% | 4.815% | 12.496% | 4.816% | constrained |
| VibeVoice streaming 7B, unpaced | Unpaced | 32.627% | 16.838% | 32.627% | 16.842% | constrained |
| VibeVoice streaming 1.5B, unpaced | Unpaced | 32.669% | 16.952% | 32.669% | 16.956% | constrained |
| VibeVoice streaming 1.5B, paced | Real-time paced | 32.947% | 17.210% | 32.947% | 17.215% | constrained |
| VibeVoice streaming 7B, paced | Real-time paced | 33.808% | 18.032% | 33.808% | 18.036% | constrained |

Unpaced = saved audio processed without waiting. Two-speaker correction uses the complete output after the stream, not a live speaker-count decision. These scores do not measure latency.

## All configurations

Every approved configuration is listed below, including constrained and retrospective settings. These tables are not live leaderboards or controlled speed rankings.

<details>
<summary>Expand every approved configuration and common-interval score</summary>


### Batch / offline

Ordered by **common-interval DER at ±250 ms**, lowest first. Speaker policies still differ.

| System | Speaker policy | Whole DER, zero | Whole DER, ±250 ms | Common DER, zero | Common DER, ±250 ms | Whole-file count accuracy | Speed |
|---|---|---:|---:|---:|---:|---:|---|
| Pyannote Precision-2 API | Known 2 | 11.004% | 2.823% | 10.986% | 2.824% | constrained | 12 s/file, API round trip |
| Pyannote Precision-3 API | Known 2 | 11.592% | 2.884% | 11.597% | 2.888% | constrained | 18 s/file, API round trip |
| Pyannote Precision-3 API | Automatic | 11.597% | 2.891% | 11.601% | 2.895% | 93.3% | 19 s/file, API round trip |
| Sortformer v1, 180 s windows, FP32 | Folded to 2 after inference | 12.706% | 3.159% | 12.706% | 3.159% | constrained | 1.74 s/file (274×), L4, 1 file at a time |
| Sortformer v2.1, 30.4 s preset, FP32 | Folded to 2 after inference | 11.407% | 3.945% | 11.407% | 3.946% | constrained | 1.10 s/file (402×), L4, 1 file at a time |
| Pyannote Community-1, whole-file | Known 2; folded to 2 | 15.856% | 6.323% | 15.855% | 6.325% | constrained | 18.52 s/file (31×), L4, 1 file at a time |
| VibeVoice-ASR, native batch | Automatic | 24.191% | 8.233% | 24.191% | 8.235% | 100.0% | 123 s/file, joint ASR+diarization server |
| Meta Muse Voice Transcribe | Automatic per request | 29.169%\* | 13.042%\* | 29.169% | 13.042% | 90.0%\* | 92 s/request, API round trip |

\* **Muse:** starred cells use the same **20 independently scored intervals** as its common-interval results, not whole-recording scores. Five recordings were split at the API's 10-minute limit; speaker-count accuracy is **18/20 intervals (90%)**. Speaker identity across chunk boundaries is not evaluated.

### Streaming diarization

Ordered by **common-interval DER at ±250 ms**, lowest first. Speaker policies still differ.

| System | Input pacing | Speaker policy | Whole DER, zero | Whole DER, ±250 ms | Common DER, zero | Common DER, ±250 ms | Whole-file count accuracy | Speed |
|---|---|---|---:|---:|---:|---:|---:|---|
| Pyannote live API | Real-time paced | Automatic | 10.515% | 3.959% | 10.515% | 3.960% | 66.7% | paced at 1× audio speed by design; latency not measured |
| Sortformer v2.1, 1.04 s preset, unpaced, FP32 | Unpaced | Folded to 2 after inference | 12.496% | 4.815% | 12.496% | 4.816% | constrained | 36.35 s/file (16×), L4, 1 file at a time |
| VibeVoice streaming 7B, unpaced | Unpaced | Automatic | 32.627% | 16.838% | 32.627% | 16.842% | 93.3% | — |
| VibeVoice streaming 1.5B, unpaced | Unpaced | Automatic | 32.669% | 16.952% | 32.669% | 16.956% | 100.0% | — |
| VibeVoice streaming 1.5B, paced | Real-time paced | Automatic | 32.947% | 17.210% | 32.947% | 17.215% | 100.0% | — |
| VibeVoice streaming 7B, paced | Real-time paced | Automatic | 33.808% | 18.032% | 33.808% | 18.036% | 86.7% | — |

**Speed in this table:** unpaced replay of the chunk loop on one L4, batch size 1; it is throughput of the streaming preset on saved audio, not live latency.

**Input pacing:** real-time paced runs receive audio at normal speaking speed; unpaced runs process prerecorded audio without that timing constraint. DER measures diarization accuracy, not live latency. Speaker constraints remain specific to each row.

### Omi runtime, batch (separate; not reproducible with the public adapters)

Ordered by **common-interval DER at ±250 ms**, lowest first. Speaker policies still differ.

| System | Speaker policy | Whole DER, zero | Whole DER, ±250 ms | Common DER, zero | Common DER, ±250 ms | Whole-file count accuracy | Speed |
|---|---|---:|---:|---:|---:|---:|---|
| Sortformer v1, 180 s windows + Omi, known-two | Folded to 2 after inference | 12.706% | 3.159% | 12.706% | 3.159% | constrained | 1.75 s/file (284×), L4, 1 file at a time |
| Sortformer v2.1, Omi runtime, supplementary known-two | Folded to 2 after inference | 12.173% | 3.610% | 12.173% | 3.611% | constrained | 1.88 s/file (310×), L4, 1 file at a time |
| Pyannote Community-1 + Omi | Known 2 | 15.006% | 5.407% | 15.006% | 5.408% | constrained | 1.28 s/file (466×), L4, 1 file at a time |
| Pyannote Community-1 + Omi | Automatic | 15.059% | 5.435% | 15.059% | 5.436% | 93.3% | 0.78 s/file (736×), L4, 1 file at a time |

**Omi runtime rows:** same weights, recordings and scorer, with Omi’s proprietary runtime. These are not vanilla-model results. Configurations were developed on this evaluation set. See [methodology](../docs/METHODOLOGY.md#omi-runtime-rows).

### Omi runtime, realtime (separate; not reproducible with the public adapters)

Ordered by **common-interval DER at ±250 ms**, lowest first. Speaker policies still differ.

| System | Input pacing | Speaker policy | Whole DER, zero | Whole DER, ±250 ms | Common DER, zero | Common DER, ±250 ms | Whole-file count accuracy | Speed |
|---|---|---|---:|---:|---:|---:|---:|---|
| Sortformer v2.1, streaming preset + Omi, retrospective known-two | Unpaced | Folded to 2 after inference | 14.990% | 4.369% | 14.990% | 4.370% | constrained | 35.33 s/file (16×), L4, 1 file at a time |

**Omi runtime rows:** same weights, recordings and scorer, with Omi’s proprietary runtime. These are not vanilla-model results. Configurations were developed on this evaluation set. See [methodology](../docs/METHODOLOGY.md#omi-runtime-rows).

**Speed in this table:** unpaced replay of the chunk loop on one L4, batch size 1; it is throughput of the streaming preset on saved audio, not live latency.

**Output policy:** supplementary constrained rows apply retrospective processing to the completed replay. Headline Omi live rows score the speaker revisions delivered during the stream, with automatic counts.

**Input pacing:** real-time paced runs receive audio at normal speaking speed; unpaced runs process prerecorded audio without that timing constraint. DER measures diarization accuracy, not live latency. Speaker constraints remain specific to each row.

</details>

See [comparison rules](../docs/COMPARISON.md), [methodology](../docs/METHODOLOGY.md) and [settings log](best_settings_receipt.json).
