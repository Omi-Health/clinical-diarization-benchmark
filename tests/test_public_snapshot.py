import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_private_rows_disclose_only_aggregate_results():
    snapshot = json.loads((ROOT / "results/snapshot.json").read_text())
    assert not [m for m in snapshot["models"] if m["key"].startswith("model_x") or "preview" in m["model"].lower()]
    for model in snapshot["models"]:
        assert model["public_outputs"] and (ROOT / "data/hypotheses" / model["key"]).is_dir()
    run = json.loads((ROOT / "results/ga-20260924/snapshot.json").read_text())
    private = {arm for arm, body in run["arms"].items() if "omi" in arm or "live" in arm}
    assert private == {"ga_omi_graph", "ga_live_graph", "v1_omi_tf32", "v21_omi_tf32", "v21_live_tf32"}
    for arm, body in run["arms"].items():
        for view in body["views"].values():
            for panel in view.values():
                for collar in panel.values():
                    assert set(collar) == {"aggregate"}
        assert (ROOT / "data/hypotheses/ga-20260924" / arm).is_dir() == (arm not in private)



def test_timing_data_contains_no_transcript_text():
    for directory in ["data/references", "data/hypotheses", "data/policy_inputs"]:
        for path in (ROOT / directory).rglob("*.json"):
            body = json.loads(path.read_text())
            assert set(body) == {"segments"}
            for segment in body["segments"]:
                assert set(segment) == {"start", "end", "speaker"}
