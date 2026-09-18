"""Compare a rerun with the published integer counts; never update the snapshot."""
import argparse
import json
from pathlib import Path
from clinical_diarization.score import score, aggregate, COUNTS

ROOT = Path(__file__).resolve().parents[1]


def compare(output, key, expected=None):
    manifest = json.loads((ROOT/'data/manifest.json').read_text())
    snapshot = json.loads((ROOT/'results/snapshot.json').read_text())
    model = next(m for m in snapshot['models'] if m['key'] == key)
    expected = expected or model
    differences, checked = [], 0
    for panel, cases in [('full_recordings', manifest['recordings']), ('common_scoring_intervals', manifest['common_intervals'])]:
        for collar in ('0', '0.25'):
            rows = []
            known = {r['case']: r for r in expected[panel][collar].get('rows', [])}
            for case in cases:
                source = case.get('source_case', case['case'])
                hyp = json.loads((output/'full_recordings'/f'{source}.json').read_text())['segments']
                duration = case.get('audio_duration_s', case.get('duration_s'))
                if panel == 'common_scoring_intervals':
                    clipped = []
                    for s in hyp:
                        a, b = max(0, s['start']-case['offset_s']), min(duration, s['end']-case['offset_s'])
                        if b > a:
                            clipped.append(dict(start=a, end=b, speaker=s['speaker']))
                    hyp = clipped
                ref = json.loads((ROOT/'data/references'/panel/f"{case['case']}.json").read_text())['segments']
                row = score(ref, hyp, duration, float(collar))
                rows.append(row)
                if case['case'] in known:
                    for field in (*COUNTS, 'ref_speaker_count', 'hyp_speaker_count'):
                        if field in known[case['case']] and row[field] != known[case['case']][field]:
                            differences.append(dict(panel=panel, collar=collar, case=case['case'], field=field,
                                actual=row[field], expected=known[case['case']][field]))
                checked += 1
            total = aggregate(rows)
            total['speaker_count_accuracy'] = sum(r['speaker_count_correct'] for r in rows)/len(rows)
            for field in (*COUNTS, 'speaker_count_accuracy'):
                target = expected[panel][collar]['aggregate'][field]
                if total[field] != target:
                    differences.append(dict(panel=panel, collar=collar, case='aggregate', field=field, actual=total[field], expected=target))
    return dict(scored_cases=checked, individual_expected_counts=bool(expected['full_recordings']['0'].get('rows')),
                differences=differences)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--snapshot-key', required=True)
    p.add_argument('--expected', type=Path, help='Optional privately supplied per-case scores')
    args = p.parse_args()
    expected = json.loads(args.expected.read_text()) if args.expected else None
    result = compare(args.output, args.snapshot_key, expected)
    print(json.dumps(result, indent=2))
    raise SystemExit(bool(result['differences']))


if __name__ == '__main__':
    main()
