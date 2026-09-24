"""Recompute every public output's integer counts and verify exported file hashes."""
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from clinical_diarization.score import score, COUNTS


def main():
    hashes = json.loads((ROOT / "results/file_hashes.json").read_text())
    for name, expected in hashes.items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == expected, name
    snapshot = json.loads((ROOT / "results/snapshot.json").read_text())
    checked = 0
    for model in snapshot["models"]:
        for panel in ["full_recordings", "common_scoring_intervals"]:
            for collar, body in model[panel].items():
                totals = body["aggregate"]
                assert totals["error_frames"] == sum(totals[k] for k in COUNTS[1:4])
                assert totals["der"] == totals["error_frames"] / totals["reference_frames"]
                if not model["public_outputs"]:
                    continue
                for row in body["rows"]:
                    name = row["case"] + ".json"
                    ref = json.loads((ROOT / "data/references" / panel / name).read_text())["segments"]
                    hyp = json.loads((ROOT / "data/hypotheses" / model["key"] / panel / name).read_text())["segments"]
                    actual = score(ref, hyp, row["audio_s"], float(collar))
                    for field in (*COUNTS, "hyp_speaker_count", "ref_speaker_count"):
                        assert actual[field] == row[field], (model["key"], panel, collar, name, field, actual[field], row[field])
                    checked += 1
                for field in COUNTS:
                    assert sum(r[field] for r in body["rows"]) == totals[field]
        print(f"{model['model']}: {'output scores verified' if model['public_outputs'] else 'aggregate arithmetic only; private outputs'}", flush=True)
    print(f"Verified {checked} recording/interval/collar scores; {len(hashes)} file hashes.")


if __name__ == "__main__":
    main()
