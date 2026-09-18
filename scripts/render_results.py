"""Render tables from the reviewed numeric snapshot, without hand-entered scores."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


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
        return f"{s['median_s_per_file']:.1f} s/file ({s['x_realtime']:.0f}×), L4 batch"
    if s.get("kind") == "api_round_trip":
        unit = s.get("unit", "file")
        return f"{s['median_s_per_file']:.0f} s/{unit}, API round trip"
    if s.get("kind") == "joint_server":
        return f"{s['median_s_per_file']:.0f} s/file, joint ASR+diarization server"
    return "—"


def table_lines(snapshot, heading_level=2, compact=False):
    lines = []
    for groups, title in [({"batch"}, "Batch / offline"), ({"paced_streaming", "supplemental_unpaced"}, "Streaming diarization")]:
        streaming = "paced_streaming" in groups
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
            pacing = ["Real-time paced" if model["group"] == "paced_streaming" else "Unpaced"] if streaming else []
            lines.append("| " + " | ".join([model["model"], *pacing, model["speaker_policy"], *cells, count, speed_cell(model["key"])]) + " |")
        if streaming:
            lines += ["", "**Speed in this table:** unpaced replay of the chunk loop on one L4, batch size 1; it is throughput of the streaming preset on saved audio, not live latency."]
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
    best = json.loads((ROOT/'results/snapshot.json').read_text())
    paired = json.loads((ROOT/'results/speaker_policy_snapshot.json').read_text())
    best_note = 'Best tested configurations on this dataset, with measured speed. Speaker constraints and decoding differ by row; the controlled comparison below isolates speaker policy.'
    paired_note = 'Each pair uses the same saved automatic output, unchanged or folded to at most two speakers with the same function. NVIDIA pairs use FP32 and native decoding (v1 uses 180 s windows).'
    timing_note = 'Speed scopes differ: local L4 processing, API round trips, or joint ASR plus diarization. See [timing details](docs/METHODOLOGY.md#speed).'
    lines = ['# Diarization results', '',
             'Same 15 PriMock consultations, 2.4152 audio hours. Updated 2026-09-19.', '',
             'DER ↓ is better. Ranked by common-interval DER at ±250 ms. Omi’s proprietary runtime is not included. Model X remains aggregate-only.', '',
             '## Best-tested settings and speed', '', best_note, '', timing_note.replace('(docs/', '(../docs/')]
    lines += table_lines(best, heading_level=3)
    lines += ['', '## Controlled speaker-policy comparison', '', paired_note, '',
              'Precision-2 only has a known-two API run and appears in the best-tested table above. The tuned Model X streaming result also appears there; it changes thresholds and drops extra speakers, so it is separate from the identical-fold comparison below.']
    lines += paired_tables(paired, heading_level=3)
    lines += ['', 'See [methodology](../docs/METHODOLOGY.md), [paired score counts](speaker_policy_snapshot.json), [settings log](best_settings_receipt.json), and [run instructions](../inference/README.md).', '']
    (ROOT/'results/RESULTS.md').write_text('\n'.join(lines))
    featured = {'model_x_streaming_unpaced', 'sortformer21_low_unpaced'}
    def featured_rows(snapshot):
        return {**snapshot, 'models': [m for m in snapshot['models'] if m['group'] != 'supplemental_unpaced' or m['key'] in featured]}
    generated = [f"**Dataset:** 15 mock consultations, {paired['audio_hours']:.4f} audio hours · **Updated:** {paired['snapshot_date']}", '',
                 '**DER ↓** = speaker diarization error. Ranked by common-interval DER at ±250 ms.', '',
                 '### Best-tested settings and speed', '', best_note, '', timing_note]
    generated += table_lines(featured_rows(best), heading_level=4, compact=True)
    generated += ['', '### Controlled speaker-policy comparison', '', paired_note]
    generated += paired_tables(featured_rows(paired), heading_level=4, compact=True)
    generated += ['', 'Additional unpaced VibeVoice runs and all settings are in the [detailed results](results/RESULTS.md).']
    p = ROOT/'README.md';readme = p.read_text();a = '<!-- BENCHMARK:START -->';b = '<!-- BENCHMARK:END -->'
    before, rest = readme.split(a);_, after = rest.split(b)
    p.write_text(before + a + '\n\n' + '\n'.join(generated) + '\n\n' + b + after)


if __name__ == '__main__':
    main()
