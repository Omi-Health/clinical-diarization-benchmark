import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_published_native_run_matches_supplied_code_and_configs():
    receipt = json.loads((ROOT/'results/native_l4_receipt.json').read_text())
    assert len(receipt['models']) == 3
    assert receipt['environment_constraints_sha256'] == digest(ROOT/'inference/environment-constraints.txt')
    assert receipt['dockerfile_sha256'] == digest(ROOT/'inference/Dockerfile')
    for key, run in receipt['models'].items():
        p = ROOT / run.get('configuration_at_run', f'inference/configs/{key}.json')
        config = json.loads(p.read_text())
        assert config['mode'] == 'native'
        assert config['precision'] == 'bf16'
        assert not config.get('fold_to') and not config.get('postprocessing')
        assert run['configuration_sha256'] == digest(p)
        assert run['runner_sha256'] == receipt.get('runner_sha256_at_run', digest(ROOT/'inference/run.py'))
        assert run['processing_sha256'] == digest(ROOT/'inference/processing.py')
        assert run['manifest_sha256'] == digest(ROOT/'data/manifest.json')
        assert run['device'] == 'NVIDIA L4'
        assert run['recordings'] == 15 and run['completed']
        assert run['parameter_dtype'] == 'torch.bfloat16'
    versions = {(r['python'], r['torch'], r['nemo']) for r in receipt['models'].values()}
    assert len(versions) == 1
