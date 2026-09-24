"""Independently score whole recordings in continuous time with pyannote.metrics.

Install the 'crosscheck' extra. Optionally use --private-runs DIR to check private Omi-runtime
outputs locally; predictions and model identity are never written by this script.
"""
import argparse
import json
import sys
from pathlib import Path
from pyannote.core import Annotation, Segment, Timeline
from pyannote.metrics.diarization import DiarizationErrorRate

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def annotation(path):
    return annotation_segments(json.loads(Path(path).read_text())['segments'])


def annotation_segments(segments):
    ann = Annotation()
    for s in segments:
        if s['end'] > s['start']:
            # Distinct tracks preserve two speakers with identical boundaries.
            ann[Segment(s['start'], s['end']), s['speaker']] = s['speaker']
    return ann


def crosscheck(private_runs=None, speaker_policies=False):
    snapshot = json.loads((ROOT/'results/snapshot.json').read_text())
    if speaker_policies:
        paired = json.loads((ROOT/'results/speaker_policy_snapshot.json').read_text())
        snapshot = dict(models=[dict(key=m['key'], public_outputs=m['public_outputs'],
            source=m.get('source'), policy=policy, **panels)
            for m in paired['models'] for policy, panels in m['policies'].items()])
    cases = json.loads((ROOT/'data/manifest.json').read_text())['recordings']
    references = {c['case']: annotation(ROOT/'data/references/full_recordings'/f"{c['case']}.json") for c in cases}
    results = []
    for model in snapshot['models']:
        if not model['full_recordings']:
            continue
        if model['public_outputs']:
            directory = (ROOT/model['source'] if speaker_policies else ROOT/'data/hypotheses'/model['key'])/'full_recordings'
        elif private_runs is not None:
            directory = private_runs/model['key']/'full_recordings'
        else:
            continue
        # Missing cases are errors, never a silently reduced evaluation subset.
        if speaker_policies:
            from inference.speaker_policies import policy_segments
            hypotheses = {c['case']: annotation_segments(policy_segments(
                json.loads((directory/f"{c['case']}.json").read_text())['segments'], model['policy'])).support() for c in cases}
        else:
            hypotheses = {c['case']: annotation(directory/f"{c['case']}.json").support() for c in cases}
        row = dict(key=model['key'])
        if speaker_policies:
            row['policy'] = model['policy']
        for key, collar in [('0', 0.0), ('0.25', 0.5)]:
            metric = DiarizationErrorRate(collar=collar, skip_overlap=False)
            for c in cases:
                metric(references[c['case']], hypotheses[c['case']],
                       uem=Timeline([Segment(0, c['audio_duration_s'])]))
            expected = model['full_recordings'][key]['aggregate']['der']
            row[key] = dict(pyannote_der=abs(metric), snapshot_der=expected,
                            difference_percentage_points=100*(abs(metric)-expected))
        results.append(row)
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--private-runs', type=Path)
    parser.add_argument('--speaker-policies', action='store_true', help='Check the current matched-policy tables')
    args = parser.parse_args()
    rows = crosscheck(args.private_runs, args.speaker_policies)
    print(json.dumps(rows, indent=2))
    worst = max(abs(r[c]['difference_percentage_points']) for r in rows for c in ['0', '0.25'])
    print(f'Largest difference: {worst:.6f} percentage points')
    # At zero collar, dense boundaries amplify the 10 ms discretization difference.
    raise SystemExit(0 if worst < .5 else 1)


if __name__ == '__main__':
    main()
