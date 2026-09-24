"""Verify paired speaker policies from the public automatic outputs."""
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from inference.speaker_policies import score_policy
from clinical_diarization.score import COUNTS


def main():
    snapshot = json.loads((ROOT/'results/speaker_policy_snapshot.json').read_text())
    checked = 0
    for model in snapshot['models']:
        for policy, panels in model['policies'].items():
            actual = score_policy(ROOT/model['source'], policy, model.get('interval_only', False)) if model['public_outputs'] else None
            for panel, bodies in panels.items():
                for collar, body in bodies.items():
                    a = body['aggregate']
                    assert a['error_frames'] == sum(a[k] for k in COUNTS[1:4])
                    assert a['der'] == a['error_frames']/a['reference_frames']
                    if actual is not None:
                        assert actual[panel][collar] == body, (model['key'], policy, panel, collar)
                        checked += len(body['rows'])
                    else:
                        assert set(body) == {'aggregate'}
            print(model['key'], policy, 'verified' if actual else 'aggregate arithmetic only', flush=True)
    print(f'Verified {checked} paired-policy scores.')


if __name__ == '__main__':
    main()
