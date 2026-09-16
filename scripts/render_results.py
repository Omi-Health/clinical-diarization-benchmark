"""Render tables from the reviewed numeric snapshot, without hand-entered scores."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    snapshot = json.loads((ROOT / "results/snapshot.json").read_text())
    lines = ["# Diarization results", "", "Snapshot: 2026-09-17. Same 15 PriMock mock consultations, 2.4152 audio hours.", "",
             "DER ↓ is a percentage; lower is better. Speaker policies differ and are part of each result. These are historical system configurations, not a controlled model-only ranking."]
    for group, title in [("batch", "Batch / offline"), ("paced_streaming", "Real-time-paced streaming"), ("supplemental_unpaced", "Supplementary: streaming checkpoints run unpaced")]:
        lines += ["", "## " + title, "",
                  "| System | Speaker policy | Whole DER, zero | Whole DER, ±250 ms | Common DER, zero | Common DER, ±250 ms | Whole-file count accuracy |",
                  "|---|---|---:|---:|---:|---:|---:|"]
        for model in snapshot["models"]:
            if model["group"] != group:
                continue
            cells = []
            for panel in ["full_recordings", "common_scoring_intervals"]:
                for collar in ["0", "0.25"]:
                    p = model[panel].get(collar)
                    cells.append(f"{100*p['aggregate']['der']:.3f}%" if p else "—")
            full = model["full_recordings"].get("0")
            count = "constrained" if model["speaker_policy"] != "Automatic" else (f"{100*full['aggregate']['speaker_count_accuracy']:.1f}%" if full else "—")
            if not full:
                count = "—"
            lines.append("| " + " | ".join([model["model"], model["speaker_policy"], *cells, count]) + " |")
    lines += ["", "## Reading the results", "",
              "- **Model X:** anonymized system. Aggregate results only; its inference code, configuration and individual outputs are private. The public repo cannot independently reproduce this row.",
              "- **±250 ms** means a 250 ms exclusion radius around each reference boundary (pyannote total collar **0.5 seconds**). Zero collar is also shown. This is a 10 ms frame scorer, not a claim of bitwise parity with a continuous-time scorer.",
              "- **Common intervals:** the same 20 scoring intervals for every system. Muse required five long recordings to be split at 600 seconds. Matching is independent in each interval. Inference context remains different, and cross-interval speaker continuity is not measured.",
              "- **Known/folded to 2:** these rows use information that automatic-count rows do not. A correct count for a constrained run does not demonstrate automatic speaker counting.",
              "- **References:** frozen VAD-corrected timing annotations derived from PriMock57. Overlap and false alarms during silence are included. These are not hand-verified word-level speech boundaries.",
              "- VibeVoice uses its returned timing, including coarse/chunk-derived boundaries. Speaker-labelled pauses count as false alarms; no reference-based silence mask repairs the predictions.",
              "- No speed ranking: these systems perform different work (diarization alone versus ASR plus diarization), on different hardware or remote APIs.",
              "", "See [methodology](../docs/METHODOLOGY.md), [data attribution](../data/ATTRIBUTION.md), and [numeric snapshot](snapshot.json).", ""]
    (ROOT / "results/RESULTS.md").write_text("\n".join(lines))


if __name__ == "__main__":
    main()
