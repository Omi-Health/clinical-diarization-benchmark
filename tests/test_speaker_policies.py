import json
import hashlib
from pathlib import Path
from inference.speaker_policies import policy_segments, score_policy
from inference.processing import normalize_max_speakers

ROOT = Path(__file__).resolve().parents[1]


def test_same_fold_preserves_all_extra_speech():
    segments = [dict(start=0, end=4, speaker='a'), dict(start=4, end=7, speaker='b'),
                dict(start=7, end=8, speaker='c')]
    assert policy_segments(segments, 'automatic') == segments
    folded = policy_segments(segments, 'fold_two')
    assert folded == normalize_max_speakers(segments, 2)
    assert [(s['start'], s['end']) for s in folded] == [(s['start'], s['end']) for s in segments]
    assert folded[-1]['speaker'] == 'spk_1'


def test_fold_uses_whole_recording_before_interval_clipping(tmp_path, monkeypatch):
    import inference.speaker_policies as module
    monkeypatch.setattr(module, 'ROOT', tmp_path)
    data = tmp_path/'data';data.mkdir()
    (data/'manifest.json').write_text(json.dumps(dict(recordings=[dict(case='a', audio_duration_s=10)],
        common_intervals=[dict(case='part', source_case='a', offset_s=8, duration_s=2)])))
    for panel, case, segs in [('full_recordings', 'a', [dict(start=0,end=10,speaker='ref')]),
                             ('common_scoring_intervals','part',[dict(start=0,end=2,speaker='ref')])]:
        p=data/'references'/panel;p.mkdir(parents=True)
        (p/f'{case}.json').write_text(json.dumps(dict(segments=segs)))
    out=tmp_path/'run/full_recordings';out.mkdir(parents=True)
    (out/'a.json').write_text(json.dumps(dict(segments=[dict(start=0,end=8,speaker='a'),
        dict(start=8,end=9,speaker='b'),dict(start=9,end=10,speaker='c')])))
    # Full-file folding maps b and c onto the same retained speaker; folding the clipped
    # interval instead would keep b and c separate and get this count wrong.
    folded=score_policy(out.parent,'fold_two')
    assert folded['common_scoring_intervals']['0']['rows'][0]['hyp_speaker_count']==1


def test_paired_snapshot_is_matched_and_public():
    snapshot=json.loads((ROOT/'results/speaker_policy_snapshot.json').read_text())
    for m in snapshot['models']:
        assert set(m['policies']) == {'automatic','fold_two'}
        if 'configuration' in m:
            path=ROOT/m['configuration']
            assert hashlib.sha256(path.read_bytes()).hexdigest()==m['configuration_sha256']
            config=json.loads(path.read_text())
            assert config['precision']=='fp32' and not config.get('fold_to')
            assert config['mode'] in {'native','legacy_windowed'}
        assert not m['key'].startswith('model_x')
        assert m['public_outputs'] and (ROOT/m['source']).is_dir()
