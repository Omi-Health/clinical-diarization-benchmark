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
        assert config.exists() and json.loads(config.read_text())['precision'] == 'fp32'
        assert run['parameter_dtype'] == 'torch.float32' and run['fold_to'] == 2 and run['recordings'] == 15
        assert 'Model X' not in config.read_text() or key.startswith('model_x')
