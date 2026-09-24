"""Render tables from the reviewed numeric snapshot, without hand-entered scores."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def speed_cell(key):
    """Batch processing speed from results/best_settings_receipt.json, when measured for this row."""
    try:
        speed = json.loads((ROOT / "results/best_settings_receipt.json").read_text()).get("speed", {})
    except FileNotFoundError:
        return "—"
    s = speed.get(key)
    if not s:
        return "—"
    if s.get("kind") == "l4_batch":
        return f"{s['median_s_per_file']:.2f} s/file ({s['x_realtime']:.0f}×), L4, 1 file at a time"
    if s.get("kind") == "api_round_trip":
        unit = s.get("unit", "file")
        return f"{s['median_s_per_file']:.0f} s/{unit}, API round trip"
    if s.get("kind") == "joint_server":
        return f"{s['median_s_per_file']:.0f} s/file, joint ASR+diarization server"
    if s.get("kind") == "paced_live":
        return "paced at 1× audio speed by design; latency not measured"
    return "—"


# Selection is by documented implementation, not the lowest observed DER.
BATCH_PAIRS = [
    ("Sortformer v1", "sortformer1", "sortformer1_omi_runtime"),
    ("Sortformer v2.1", "sortformer21", "sortformer21_omi_runtime"),
    ("Community-1", "community1", "community1_omi_runtime"),
    ("VibeVoice-ASR", "vibe_original", None),
]
DELIVERED_KEYS = ("pyannote_live", "vibe_15b_paced", "vibe_7b_paced")
REPLAY_KEYS = ("sortformer21_low_unpaced", "sortformer21_low_omi_runtime",
               "vibe_15b_unpaced", "vibe_7b_unpaced")


def comparison_row(model, implementation, panel="full_recordings", family=None, note=""):
    body = model[panel]
    count = "constrained"
    if model["speaker_policy"].startswith("Automatic"):
        agg = body["0"]["aggregate"]
        n = agg.get("records", 20 if panel == "common_scoring_intervals" else 15)
        count = f"{round(n * agg['speaker_count_accuracy'])}/{n}"
    cells = [family or model["model"], implementation, model["speaker_policy"],
             f"{100*body['0']['aggregate']['der']:.3f}%",
             f"{100*body['0.25']['aggregate']['der']:.3f}%", count,
             speed_cell(model["key"]), note]
    return "| " + " | ".join(cells) + " |"


def comparison_lines(snapshot=None, heading_level=2):
    # Headline tables come from the 24 September L4 run; the full snapshot feeds the configuration tables.
    from scripts.ga_tables import comparison_lines as current
    return current(heading_level)


def table_lines(snapshot, heading_level=2, compact=False):
    lines = []
    for groups, title in [({"batch"}, "Batch / offline"), ({"paced_streaming", "supplemental_unpaced"}, "Streaming diarization"), ({"omi_runtime_batch"}, "Omi runtime, batch (separate; not reproducible with the public adapters)"), ({"omi_runtime_realtime"}, "Omi runtime, realtime (separate; not reproducible with the public adapters)")]:
        streaming = "paced_streaming" in groups or groups == {"omi_runtime_realtime"}
        pacing_header = " Input pacing |" if streaming else ""
        pacing_separator = "---|" if streaming else ""
        lines += ["", "#" * heading_level + " " + title, "",
                  *([] if compact else ["Ordered by **common-interval DER at ±250 ms**, lowest first. Speaker policies still differ.", ""]),
                  f"| System |{pacing_header} Speaker policy | Whole DER, zero | Whole DER, ±250 ms | Common DER, zero | Common DER, ±250 ms | Whole-file count accuracy | Speed |",
                  f"|---|{pacing_separator}---|---:|---:|---:|---:|---:|---|"]
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
            pacing = [model.get("pacing", "Real-time paced" if model["group"] == "paced_streaming" else "Unpaced")] if streaming else []
            lines.append("| " + " | ".join([model["model"], *pacing, model["speaker_policy"], *cells, count, speed_cell(model["key"])]) + " |")
        if groups in ({"omi_runtime_batch"}, {"omi_runtime_realtime"}):
            lines += ["", "**Omi runtime rows:** same weights, recordings and scorer, with Omi’s proprietary runtime. These are not vanilla-model results. Configurations were developed on this evaluation set. See [methodology](../docs/METHODOLOGY.md#omi-runtime-rows)."]
        if streaming:
            lines += ["", "**Speed in this table:** unpaced replay of the chunk loop on one L4, batch size 1; it is throughput of the streaming preset on saved audio, not live latency."]
        if groups == {"omi_runtime_realtime"}:
            lines += ["", "**Output policy:** supplementary constrained rows apply retrospective processing to the completed replay. Headline Omi live rows score the speaker revisions delivered during the stream, with automatic counts."]
        if streaming:
            lines += ["", ("**Pacing:** real-time = normal speaking speed; unpaced = processed without waiting. Scores measure accuracy, not live latency." if compact else "**Input pacing:** real-time paced runs receive audio at normal speaking speed; unpaced runs process prerecorded audio without that timing constraint. DER measures diarization accuracy, not live latency. Speaker constraints remain specific to each row.")]
        if any(model["key"] == "muse" for model in models):
            lines += ["", ("\\* Muse's starred values are interval results, not whole-recording results; count accuracy is 18/20 intervals." if compact else "\\* **Muse:** starred cells use the same **20 independently scored intervals** as its common-interval results, not whole-recording scores. Five recordings were split at the API's 10-minute limit; speaker-count accuracy is **18/20 intervals (90%)**. Speaker identity across chunk boundaries is not evaluated.")]
    return lines


def paired_tables(snapshot, heading_level=2, compact=False):
    lines = []
    for groups, title in [({'batch'}, 'Batch / offline'),
                          ({'paced_streaming', 'supplemental_unpaced'}, 'Streaming diarization')]:
        streaming = 'paced_streaming' in groups
        lines += ['', '#' * heading_level + ' ' + title]
        for policy, label in [('automatic', 'Automatic speaker count'), ('fold_two', 'Same two-speaker post-processing')]:
            lines += ['', '#' * (heading_level + 1) + ' ' + label, '',
                      '| System |' + (' Input pacing |' if streaming else '') + ' Whole DER, zero | Whole DER, ±250 ms | Common DER, zero | Common DER, ±250 ms | Count accuracy |',
                      '|---|' + ('---|' if streaming else '') + '---:|---:|---:|---:|---:|']
            models = sorted((m for m in snapshot['models'] if m['group'] in groups),
                            key=lambda m: (policy == 'automatic' and m['key'] == 'sortformer1',
                                           m['policies'][policy]['common_scoring_intervals']['0.25']['aggregate']['der']))
            for m in models:
                panels = m['policies'][policy]
                cells = []
                for panel in ['full_recordings', 'common_scoring_intervals']:
                    for collar in ['0', '0.25']:
                        body = panels[panel].get(collar)
                        fallback = not body and m.get('interval_only')
                        if fallback:
                            body = panels['common_scoring_intervals'][collar]
                        cells.append(f"{100 * body['aggregate']['der']:.3f}%" + ('\\*' if fallback else ''))
                body = panels['full_recordings'].get('0') or panels['common_scoring_intervals']['0']
                count = 'constrained' if policy == 'fold_two' else f"{100 * body['aggregate']['speaker_count_accuracy']:.1f}%" + ('\\*' if m.get('interval_only') else '')
                if policy == 'automatic' and m['key'] == 'sortformer1':
                    cells = ['n/a (windowed)'] * 4
                    count = 'n/a (windowed)'
                pacing = ['Real-time paced' if m['group'] == 'paced_streaming' else 'Unpaced'] if streaming else []
                lines += ['| ' + ' | '.join([m['model'], *pacing, *cells, count]) + ' |']
        if not streaming:
            lines += ['', '\\* Muse: 20 separate request intervals, not whole recordings. V1 automatic results are n/a: window stitching adds labels, so this is not a model-only counting result. Raw scores and the whole-file variant remain in the settings log.']
        else:
            lines += ['', 'Unpaced = saved audio processed without waiting. Two-speaker correction uses the complete output after the stream, not a live speaker-count decision. These scores do not measure latency.']
    return lines


def main():
    best = json.loads((ROOT / 'results/snapshot.json').read_text())
    paired = json.loads((ROOT / 'results/speaker_policy_snapshot.json').read_text())
    paired_note = ('Each pair uses the same saved automatic output, unchanged or folded to at most two '
                   'speakers with the same function. This isolates speaker-policy effects; it is not '
                   'a native-versus-Omi runtime experiment. Streaming correction is retrospective.')
    intro = ["**Dataset:** 15 mock consultations, 2.4152 audio hours · **Published:** September 2026", '',
             '**DER ↓** = diarization error, with ±250 ms excluded around reference boundaries. '
             'Main tables use automatic speaker counts. Full results retain zero-tolerance scores and constrained experiments.', '',
             'NVIDIA baselines use their pinned released checkpoints on one L4. '
             'Hosted APIs use their public endpoints. Dates and hardware are in the [measurement record](results/RESULTS.md#measurement-record). '
             '[Run and reproduction details](docs/GA_20260924.md).']
    generated = intro + [''] + comparison_lines(best, heading_level=3)
    # Paired policy tables remain on the detailed results page.
    generated += ['', 'All configurations, common-interval scores and alternative Omi settings are in the '
                  '[full configuration tables](results/RESULTS.md#all-configurations). '
                  'See the [comparison rules](docs/COMPARISON.md).']
    p = ROOT / 'README.md'
    before, rest = p.read_text().split('<!-- BENCHMARK:START -->')
    _, after = rest.split('<!-- BENCHMARK:END -->')
    p.write_text(before + '<!-- BENCHMARK:START -->\n\n' + '\n'.join(generated) +
                 '\n\n<!-- BENCHMARK:END -->' + after)
    from scripts.ga_tables import detail_lines, measurement_record_lines
    lines = ['# Diarization results', '', *intro, *comparison_lines(best), '', *detail_lines(), '', *measurement_record_lines(), '',
             '## Matched speaker-policy comparison', '', paired_note, *paired_tables(paired, heading_level=3), '',
             '## All configurations', '',
             'Every approved configuration is listed below, including constrained and retrospective settings. '
             'These tables are not live leaderboards or controlled speed rankings.', '',
             '<details>', '<summary>Expand every approved configuration and common-interval score</summary>', '']
    lines += table_lines(best, heading_level=3)
    lines += ['', '</details>', '', 'See [comparison rules](../docs/COMPARISON.md), '
              '[methodology](../docs/METHODOLOGY.md) and [settings log](best_settings_receipt.json).', '']
    (ROOT / 'results/RESULTS.md').write_text('\n'.join(lines).replace('(docs/', '(../docs/').replace('(results/RESULTS.md#', '(#'))


if __name__ == '__main__':
    main()
