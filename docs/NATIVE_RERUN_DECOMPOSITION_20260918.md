# Native rerun decomposition — 2026-09-18

Status: analysis of the 18 September native rerun (commit 7cce63b) against the archived rows, with a targeted FP32 rerun on one NVIDIA L4 in the same pinned environment (Dockerfile in `inference/`). The final snapshot uses the best tested reproducible configuration per row; the settings log records alternatives. The analysis below describes the earlier decomposition run.

Question: the archived public rows had Sortformer v1 as the best NVIDIA row (3.157 % DER at
±250 ms) and v2.1 at 3.610 %; the 18 September native L4 rerun (public commit 7cce63b) shows
v2.1 at 6.593 % and v1 at 6.778 %, now the worst NVIDIA rows. Did the models change, or the
protocol?

Answer: the protocol. Three things changed together in the rerun: speaker policy (historical
fold to two speakers → native automatic count), precision (FP32 → BF16, chosen because
whole-file FP32 v1 ran out of memory on the L4), and for v1 the inference context (180 s
windows → whole 6–14 minute recordings). Each is quantified below from saved outputs plus a
targeted rerun on a dedicated L4 in the same pinned environment (NeMo 3.1.0+2d902060e, torch
2.8.0 nv25.08, image digest as the public Dockerfile). Configurations used: `inference/configs/rerun-20260918/`. Whole-recording panel, public scorer, public references.

## Decomposition (full-recording panel, DER %, 15 PriMock consultations, all two-speaker)

| Run | Precision | Context | Native (auto count) zero / ±250 | Folded to 2 zero / ±250 | Files with 2 speakers predicted |
|---|---|---|---|---|---|
| v1 published (b454b9d) | FP32 | 180 s windows | – | 12.706 / **3.157** | (folded) |
| v1 windowed, rerun | FP32 | 180 s windows | 18.555 / 9.474 | 12.706 / **3.159** | 5/15 |
| v1 windowed, rerun | BF16 | 180 s windows | 18.541 / 9.483 | 12.689 / 3.165 | 5/15 |
| v1 whole-file (public 7cce63b) | BF16 | whole file | 14.784 / **6.778** | 14.122 / 6.143 | 14/15 |
| v2.1 published (b454b9d) | FP32 | 30.4 s preset, production path | – | 12.173 / **3.610** | (folded) |
| v2.1 offline, rerun (twice, identical) | FP32 | 30.4 s preset | 15.768 / 7.974 | 11.407 / **3.945** | 3/15 |
| v2.1 offline (public 7cce63b) | BF16 | 30.4 s preset | 14.077 / **6.593** | 12.731 / 5.392 | 1/15 |
| v2.1 1.04 s preset, rerun | FP32 | 1.04 s preset | 14.841 / 6.958 | 12.496 / 4.815 | 0/15 |
| v2.1 1.04 s preset (public 7cce63b) | BF16 | 1.04 s preset | 15.649 / 7.956 | 13.446 / 5.927 | 0/15 |
| Model X offline, rerun | FP32 | 30.4 s preset | 12.594 / 4.787 | 12.590 / 4.787 | 12/15 |
| Model X offline (public 7cce63b) | BF16 | 30.4 s preset | 12.593 / 4.786 | – | 12/15 |
| Model X 1.04 s preset, rerun | FP32 | 1.04 s preset | 12.754 / 4.947 | 12.669 / 4.865 | 7/15 |
| Model X 1.04 s preset (public 7cce63b) | BF16 | 1.04 s preset | 12.746 / 4.962 | – | 9/15 |

Folding = the repository's historical `normalize_max_speakers(…, 2)`: keep the two labels
with most speech, map the rest onto the second. Applied offline to native outputs for this decomposition. The final public runner applies folding itself when `fold_to: 2` is configured.

## What each factor does

**Sortformer v1.** The windowed FP32 rerun folded to two gives 3.159 % against the published
3.157 % (zero collar identical, 12.706 %): the public runner in the new environment
reproduces the archived row, so the environment and code are clean. BF16 changes v1 by
0.006 points: precision is irrelevant for v1. The whole-file run is what moved it: 13 of 15
recordings stay within 0.5 points of the archived values, and one recording,
day1_consultation11 (13.4 min), goes from 3.95 % to 31.76 % with two speakers predicted and
confusion in every minute of the file; the windowed run has zero confusion frames on the
same file. The v1 model card states it was trained on 90-second samples and that the maximum
test duration is memory-bound (about 12 minutes on a 48 GB GPU; FP32 whole-file v1 ran out
of memory on the L4 here). Whole-file inference on these 6–14 minute recordings is outside
that 90 s training context. Length alone does not predict the failure: the longest recording
(day1_consultation07, 14.3 min) scored 5.58 %, within 0.03 of its archived value, while
consultation11 collapsed into file-wide label confusion. One of fifteen files failing this
way, and none under the 180 s windows, supports choosing the windowed configuration on this dataset. The 180 s windows and 12 s overlap are this benchmark's adapter policy, not a model-card requirement. Longer inference is not invalid merely because training samples were 90 s. Window stitching can introduce extra labels (5/15 correct counts, 9.47 % unfolded); both policies remain useful measured results, and the selected folded row uses the known count of two.

**Sortformer v2.1.** FP32 native folded gives 3.945 %, within 0.34 points of the published
3.610 %; the remainder is the known production-path difference (the September 7 row went
through the production tenant, which the archive README leaves as not fully attributed). Two
identical FP32 runs show the runner is deterministic. Removing the fold costs 4.0 points at
FP32 (7.974 %) and 1.2 at BF16 (6.593 %), because the 4-speaker model predicts 3 or 4
speakers on 12–14 of the 15 two-person consultations. Precision matters for v2.1 but not in
one direction: at FP32 the swap lands on day1_consultation07 with 4 labels (33 %), at BF16 the
same file gets 3 labels (20 %) while the folded score worsens from 3.945 to 5.392. Under
automatic count v2.1 is unstable on this material at either precision; that difference explains the weaker native baseline; the current table uses the labelled folded result.

**Model X.** Precision-insensitive (4.787 vs 4.786) and count-stable (12/15). Its offline scores barely change under folding. This does not apply to its tuned streaming decoder, which explicitly retains the top two speakers.

## Selected comparison

The main table shows the best tested configuration reproduced with the current public runner and pinned environment. Alternatives, including native counts, BF16 and historical runs, remain in the settings log. Older archived scores can be slightly lower; they are not selected merely because their numbers are lower.

Speaker-count information differs by row, so this is a comparison of labelled configurations, not an equal-information model-only ranking. Configuration selection used these 15 recordings; the result is not a new holdout estimate or proof of the best possible setting. The 3.610 % production-path result remains archived because it has not been reproduced by the public runner; the exact cause of the gap is not fully established.


## Provenance

Seven runs with the public `inference/run.py` on one NVIDIA L4, Docker image built from the public `inference/Dockerfile` (NeMo 3.1.0+2d902060e), batch size 1, all exit 0; the v2.1 offline FP32 configuration was run twice with identical outputs. Configurations: `inference/configs/rerun-20260918/`. Model X keeps its placeholder name; its outputs stay private and only aggregates are shown.
