"""Render tables from the reviewed numeric snapshot, without hand-entered scores."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def table_lines(snapshot, heading_level=2, compact=False):
    lines = []
    for groups, title in [({"batch"}, "Batch / offline"), ({"paced_streaming", "supplemental_unpaced"}, "Streaming diarization")]:
        streaming = "paced_streaming" in groups
        pacing_header = " Input pacing |" if streaming else ""
        pacing_separator = "---|" if streaming else ""
        lines += ["", "#" * heading_level + " " + title, "",
                  *([] if compact else ["Ordered by **common-interval DER at ±250 ms**, lowest first. Speaker policies still differ.", ""]),
                  f"| System |{pacing_header} Speaker policy | Whole DER, zero | Whole DER, ±250 ms | Common DER, zero | Common DER, ±250 ms | Whole-file count accuracy |",
                  f"|---|{pacing_separator}---|---:|---:|---:|---:|---:|"]
        models = sorted(
            (model for model in snapshot["models"] if model["group"] in groups),
            key=lambda model: (model["common_scoring_intervals"]["0.25"]["aggregate"]["der"], model["model"]),
        )
        for model in models:
            cells = []
            for panel in ["full_recordings", "common_scoring_intervals"]:
                for collar in ["0", "0.25"]:
                    p = model[panel].get(collar)
                    interval_fallback = model["key"] == "muse" and not p and panel == "full_recordings"
                    if interval_fallback:
                        p = model["common_scoring_intervals"][collar]
                    cells.append((f"{100*p['aggregate']['der']:.3f}%" + ("\\*" if interval_fallback else "")) if p else "—")
            full = model["full_recordings"].get("0")
            count = "constrained" if model["speaker_policy"] != "Automatic" else (f"{100*full['aggregate']['speaker_count_accuracy']:.1f}%" if full else "—")
            if not full:
                count = "—"
                if model["key"] == "muse":
                    interval_accuracy = model["common_scoring_intervals"]["0"]["aggregate"]["speaker_count_accuracy"]
                    count = f"{100*interval_accuracy:.1f}%\\*"
            pacing = ["Real-time paced" if model["group"] == "paced_streaming" else "Unpaced"] if streaming else []
            lines.append("| " + " | ".join([model["model"], *pacing, model["speaker_policy"], *cells, count]) + " |")
        if streaming:
            lines += ["", ("**Pacing:** real-time = normal speaking speed; unpaced = processed without waiting. Scores measure accuracy, not live latency." if compact else "**Input pacing:** real-time paced runs receive audio at normal speaking speed; unpaced runs process prerecorded audio without that timing constraint. DER measures diarization accuracy, not live latency. Speaker constraints remain specific to each row.")]
        if any(model["key"] == "muse" for model in models):
            lines += ["", ("\\* Muse's starred values are interval results, not whole-recording results; count accuracy is 18/20 intervals." if compact else "\\* **Muse:** starred cells use the same **20 independently scored intervals** as its common-interval results, not whole-recording scores. Five recordings were split at the API's 10-minute limit; speaker-count accuracy is **18/20 intervals (90%)**. Speaker identity across chunk boundaries is not evaluated.")]
    return lines


def main():
    snapshot = json.loads((ROOT / "results/snapshot.json").read_text())
    lines = ["# Diarization results", "", "Snapshot: 2026-09-18. Same 15 PriMock mock consultations, 2.4152 audio hours.", "",
             "**Omi's proprietary runtime performance is not included.** These are third-party model configurations evaluated by Omi; our own runtime will be evaluated separately.", "",
             "DER ↓ is a percentage; lower is better. Speaker policies differ and are part of each result. Sortformer and Model X were rerun natively on one L4; other rows retain their recorded vendor settings."]
    lines += table_lines(snapshot)
    lines += ["", "## Reading the results", "",
              "- **Model X:** anonymized system. Aggregate results only; inference code and presets are included. Replace the placeholder model name to run; individual outputs remain private. New runs can be compared with the published aggregates.",
              "- **±250 ms** means a 250 ms exclusion radius around each reference boundary (pyannote total collar **0.5 seconds**). Zero collar is also shown. This is a 10 ms frame scorer, not a claim of bitwise parity with a continuous-time scorer.",
              "- **Common intervals:** the same 20 scoring intervals for every system. Muse required five long recordings to be split at 600 seconds. Matching is independent in each interval. Inference context remains different, and cross-interval speaker continuity is not measured.",
              "- **Known/folded to 2:** these rows use information that automatic-count rows do not. A correct count for a constrained run does not demonstrate automatic speaker counting.",
              "- **References:** frozen VAD-corrected timing annotations derived from PriMock57. Overlap and false alarms during silence are included. These are not hand-verified word-level speech boundaries.",
              "- VibeVoice uses its returned timing, including coarse/chunk-derived boundaries. Speaker-labelled pauses count as false alarms; no reference-based silence mask repairs the predictions.",
              "- No speed ranking: these systems perform different work (diarization alone versus ASR plus diarization), on different hardware or remote APIs.",
              "", "See [methodology](../docs/METHODOLOGY.md), [data attribution](../data/ATTRIBUTION.md), and [numeric snapshot](snapshot.json).", ""]
    (ROOT / "results/RESULTS.md").write_text("\n".join(lines))
    readme_path = ROOT / "README.md"
    readme = readme_path.read_text()
    start_marker = "<!-- BENCHMARK:START -->"
    end_marker = "<!-- BENCHMARK:END -->"
    if readme.count(start_marker) != 1 or readme.count(end_marker) != 1:
        raise ValueError("README must contain one benchmark marker pair")
    before, rest = readme.split(start_marker)
    _, after = rest.split(end_marker)
    hours = snapshot["audio_hours"]
    featured_unpaced = {"model_x_streaming_unpaced", "sortformer21_low_unpaced"}
    readme_snapshot = {**snapshot, "models": [
        model for model in snapshot["models"]
        if model["group"] != "supplemental_unpaced" or model["key"] in featured_unpaced
    ]}
    main_count = len(readme_snapshot["models"])
    header = (f"**Dataset**: PriMock57 ({snapshot['recordings']} mock consultations, {hours:.4f} audio hours) "
              f"| **Configurations shown**: {main_count} | **Updated**: {snapshot['snapshot_date']}")
    summary = [header, "", "**DER ↓** = speaker diarization error; lower is better. Ranked by common-interval DER at ±250 ms."]
    supplementary_count = len(snapshot["models"]) - main_count
    supplementary_link = ["", f"{supplementary_count} additional VibeVoice unpaced runs are available in the [detailed results](results/RESULTS.md#streaming-diarization)."]
    readme_tables = table_lines(readme_snapshot, heading_level=3, compact=True)
    generated = "\n".join(summary + readme_tables + supplementary_link)
    readme_path.write_text(before + start_marker + "\n\n" + generated + "\n\n" + end_marker + after)



if __name__ == "__main__":
    main()
