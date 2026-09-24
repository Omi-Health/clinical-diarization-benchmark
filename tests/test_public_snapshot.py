import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_every_model_shares_sanitized_outputs():
    snapshot = json.loads((ROOT / "results/snapshot.json").read_text())
    assert not [m for m in snapshot["models"] if m["key"].startswith("model_x") or "preview" in m["model"].lower()]
    for model in snapshot["models"]:
        assert model["public_outputs"] and (ROOT / "data/hypotheses" / model["key"]).is_dir()
    run = json.loads((ROOT / "results/ga-20260924/snapshot.json").read_text())
    for arm, body in run["arms"].items():
        assert set(body['public_view_outputs']) == set(body['views'])
        assert all((ROOT/path).is_file() for path in body['public_view_outputs'].values())
        for view in body["views"].values():
            for panel in view.values():
                for collar in panel.values():
                    assert set(collar) == {"aggregate"}



def test_timing_data_contains_no_transcript_text():
    for directory in ["data/references", "data/hypotheses", "data/policy_inputs"]:
        for path in (ROOT / directory).rglob("*.json"):
            body = json.loads(path.read_text())
            assert set(body) == {"segments"}
            for segment in body["segments"]:
                assert set(segment) == {"start", "end", "speaker"}


def test_scored_outputs_contain_only_anonymous_speaker_timelines():
    cases = {r['case'] for r in json.loads((ROOT/'data/manifest.json').read_text())['recordings']}
    paths = list((ROOT/'data/scored_outputs').rglob('*.json'))
    assert len(paths) == 100
    for path in paths:
        body = json.loads(path.read_text())
        assert set(body) == cases
        for segments in body.values():
            for segment in segments:
                assert set(segment) == {'start','end','speaker'}
                assert all(isinstance(segment[k], (int,float)) and math.isfinite(segment[k]) for k in ['start','end'])
                assert re.fullmatch(r'(?:live_)?(?:spk|speaker)_\d+', segment['speaker'])
