import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_best_settings_log_matches_published_rows():
    receipt = json.loads((ROOT/'results/best_settings_receipt.json').read_text())
    snapshot = {m['key']: m for m in json.loads((ROOT/'results/snapshot.json').read_text())['models']}
    assert set(receipt['settings_log']) == {'sortformer1', 'sortformer21', 'sortformer21_low_unpaced', 'model_x', 'model_x_streaming_unpaced'}
    for key, entries in receipt['settings_log'].items():
        assert len(entries) >= 2, key
        chosen = [e for e in entries if e.get('chosen')]
        assert len(chosen) == 1, key
        agg = snapshot[key]['full_recordings']['0.25']['aggregate']
        assert abs(100 * agg['error_frames'] / agg['reference_frames'] - chosen[0]['c250']) < 0.002, key
        for e in entries:
            assert {'setting', 'source', 'zero', 'c250'} <= set(e)
    for key, run in receipt['runs'].items():
        config = ROOT / run['configuration']
        assert config.exists() and run['recordings'] == 15 and run.get('reproduced')
        text = config.read_text()
        if key.startswith('model_x'):
            assert json.loads(text)['model_id'] == 'Model X' and 'checkpoint_sha256' not in run
        else:
            assert json.loads(text)['precision'] == 'fp32' and json.loads(text)['fold_to'] == 2
            assert run['parameter_dtype'] == 'torch.float32' and run['fold_to'] == 2
    speed = receipt['speed']
    for key, s in speed.items():
        assert s['kind'] in {'l4_batch', 'api_round_trip', 'joint_server'} and s['median_s_per_file'] > 0
        if s['kind'] == 'l4_batch':
            assert s['gpu'].startswith('NVIDIA L4') and s['batch_size'] == 1 and s['files'] == 15
