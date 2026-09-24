"""Score saved native outputs on both public panels, without changing the snapshot."""
import argparse
import json
from pathlib import Path
from clinical_diarization.score import score, aggregate

ROOT = Path(__file__).resolve().parents[1]


def clip(segments, offset, duration):
    return [dict(start=max(0, s['start']-offset), end=min(duration, s['end']-offset), speaker=s['speaker'])
            for s in segments if min(duration, s['end']-offset) > max(0, s['start']-offset)]


def score_run(output):
    manifest = json.loads((ROOT/'data/manifest.json').read_text())
    panels = {}
    for panel, cases in [('full_recordings', manifest['recordings']),
                         ('common_scoring_intervals', manifest['common_intervals'])]:
        panels[panel] = {}
        for collar in ('0', '0.25'):
            rows = []
            for case in cases:
                source = case.get('source_case', case['case'])
                hyp = json.loads((output/'full_recordings'/f'{source}.json').read_text())['segments']
                duration = case.get('audio_duration_s', case.get('duration_s'))
                if panel == 'common_scoring_intervals':
                    hyp = clip(hyp, case['offset_s'], duration)
                ref = json.loads((ROOT/'data/references'/panel/f"{case['case']}.json").read_text())['segments']
                rows.append(dict(case=case['case'], **score(ref, hyp, duration, float(collar))))
            total = aggregate(rows)
            total['speaker_count_accuracy'] = sum(r['speaker_count_correct'] for r in rows)/len(rows)
            panels[panel][collar] = dict(aggregate=total, rows=rows)
    return panels


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    print(json.dumps(score_run(args.output), indent=2, allow_nan=False))


if __name__ == '__main__':
    main()
