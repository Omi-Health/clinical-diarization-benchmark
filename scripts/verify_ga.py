"""Recompute fresh public native outputs and every derived public recipe view."""
import hashlib
import json
import math
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from inference.speaker_policies import score_policy
from inference.score_run import clip
from clinical_diarization.score import COUNTS, score, aggregate


def verify_output(path, panels):
    """Rescore sanitized saved timelines without proprietary inference code."""
    hypotheses = json.loads((ROOT/path).read_text())
    manifest = json.loads((ROOT/'data/manifest.json').read_text())
    assert set(hypotheses) == {c['case'] for c in manifest['recordings']}
    checked = 0
    for panel, cases in [('full_recordings', manifest['recordings']),
                         ('common_scoring_intervals', manifest['common_intervals'])]:
        prepared = []
        for case in cases:
            duration = case.get('audio_duration_s', case.get('duration_s'))
            hyp = hypotheses[case.get('source_case', case['case'])]
            if panel == 'common_scoring_intervals':
                hyp = clip(hyp, case['offset_s'], duration)
            ref = json.loads((ROOT/'data/references'/panel/f"{case['case']}.json").read_text())['segments']
            prepared.append((ref, hyp, duration))
        for collar, expected in panels[panel].items():
            rows = [score(ref, hyp, duration, float(collar)) for ref, hyp, duration in prepared]
            actual = aggregate(rows)
            actual['speaker_count_accuracy'] = sum(r['speaker_count_correct'] for r in rows)/len(rows)
            assert actual == expected['aggregate'], (path, panel, collar, actual, expected['aggregate'])
            checked += len(rows)
    return checked


def verify():
    snapshot = json.loads((ROOT/'results/ga-20260924/snapshot.json').read_text())
    for name, digest in snapshot['hashes'].items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest() == digest, name
    checked = 0
    for name, arm in snapshot['arms'].items():
        assert set(arm['public_view_outputs']) == set(arm['views']), name
        for view, panels in arm['views'].items():
            path = arm['public_view_outputs'][view]
            assert path in snapshot['hashes']
            checked += verify_output(path, panels)
            for panel, bodies in panels.items():
                for collar, body in bodies.items():
                    a = body['aggregate']
                    assert a['error_frames'] == sum(a[k] for k in COUNTS[1:4])
                    assert a['der'] == a['error_frames']/a['reference_frames']
                    assert 0 <= a['speaker_count_accuracy'] <= 1
                    assert a['records'] == (15 if panel == 'full_recordings' else 20)
        source = arm['public_native_output']
        if source:
            for policy, view in [('automatic', 'native'), ('fold_two', 'native_known2')]:
                actual = score_policy(ROOT/source, policy)
                for panel, bodies in actual.items():
                    for collar, body in bodies.items():
                        assert body['aggregate'] == arm['views'][view][panel][collar]['aggregate'], (name, view, panel, collar)
            if 'model_card' in arm['views']:
                assert arm['views']['model_card'] == arm['views']['native'], name
        speed = arm['speed']
        walls = [r['wall_s'] for r in arm['receipt']['rows']]
        import statistics
        assert len(walls) == 15
        assert math.isclose(statistics.median(walls), speed['median_s'], rel_tol=1e-10)
        for view, decoding in speed.get('decoding_per_file_s', {}).items():
            assert len(decoding) == len(walls)
            assert math.isclose(statistics.median(w+d for w,d in zip(walls, decoding)), speed['combined_median_s'][view], rel_tol=1e-10)
    for family, arms in snapshot['supplemental'].items():
        for arm in arms.values():
            assert arm['public_output'] in snapshot['hashes']
            checked += verify_output(arm['public_output'], arm['panels'])
    official = json.loads((ROOT/'results/ga-20260924/official_crosscheck.json').read_text())
    assert official['same_per_case_counts_as_convenience_api_with_official_decoder'] is True
    assert official['official_exit']['returncode'] == 0
    print(f'GA: {checked} public per-recording scores recomputed, including every Omi runtime view; {len(snapshot["hashes"])} hashes checked. Runtime implementation remains private.')
    return checked


if __name__ == '__main__':
    verify()
