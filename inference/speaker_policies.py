"""Score automatic outputs and the same fold-to-two operation on both panels."""
import argparse
import json
from pathlib import Path
from inference.processing import normalize_max_speakers
from inference.score_run import clip
from clinical_diarization.score import score, aggregate

ROOT = Path(__file__).resolve().parents[1]


def policy_segments(segments, policy):
    if policy == 'automatic':
        return segments
    if policy == 'fold_two':
        return normalize_max_speakers(segments, 2)
    raise ValueError(f'Unknown policy: {policy}')


def score_policy(source, policy, interval_only=False):
    manifest = json.loads((ROOT/'data/manifest.json').read_text())
    result = {'full_recordings': {}, 'common_scoring_intervals': {}}
    for panel, cases in [('full_recordings', manifest['recordings']),
                         ('common_scoring_intervals', manifest['common_intervals'])]:
        if interval_only and panel == 'full_recordings':
            continue
        prepared = []
        for case in cases:
            duration = case.get('audio_duration_s', case.get('duration_s'))
            if interval_only:
                path = source/panel/f"{case['case']}.json"
            else:
                path = source/'full_recordings'/f"{case.get('source_case', case['case'])}.json"
            hyp = policy_segments(json.loads(path.read_text())['segments'], policy)
            # Choose speakers on the whole inference output, then clip for scoring.
            if panel == 'common_scoring_intervals' and not interval_only:
                hyp = clip(hyp, case['offset_s'], duration)
            ref = json.loads((ROOT/'data/references'/panel/f"{case['case']}.json").read_text())['segments']
            prepared.append((case['case'], duration, ref, hyp))
        for collar in ('0', '0.25'):
            rows = [dict(case=name, **score(ref, hyp, duration, float(collar)))
                    for name, duration, ref, hyp in prepared]
            total = aggregate(rows)
            total['speaker_count_accuracy'] = sum(r['speaker_count_correct'] for r in rows)/len(rows)
            result[panel][collar] = dict(aggregate=total, rows=rows)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True, help='Saved automatic inference output directory')
    parser.add_argument('--policy', choices=['automatic', 'fold_two'], required=True)
    parser.add_argument('--interval-only', action='store_true')
    args = parser.parse_args()
    print(json.dumps(score_policy(args.output, args.policy, args.interval_only), indent=2))


if __name__ == '__main__':
    main()
