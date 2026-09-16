import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_model_x_discloses_only_aggregate_results():
    snapshot = json.loads((ROOT / "results/snapshot.json").read_text())
    model = next(m for m in snapshot["models"] if m["key"] == "model_x")
    assert model["model"] == "Model X"
    assert model["public_outputs"] is False
    assert set(model) == {"key", "model", "speaker_policy", "group", "public_outputs", "full_recordings", "common_scoring_intervals"}
    for panel in ["full_recordings", "common_scoring_intervals"]:
        for body in model[panel].values():
            assert set(body) == {"aggregate"}
            assert all(isinstance(value, (int, float)) for value in body["aggregate"].values())
    assert not (ROOT / "data/hypotheses/model_x").exists()


def test_timing_data_contains_no_transcript_text():
    for directory in ["data/references", "data/hypotheses"]:
        for path in (ROOT / directory).rglob("*.json"):
            body = json.loads(path.read_text())
            assert set(body) == {"segments"}
            for segment in body["segments"]:
                assert set(segment) == {"start", "end", "speaker"}
