"""Cross-check the published whole-recording DER with pyannote.metrics (continuous time).

Usage: pip install pyannote.metrics && python scripts/crosscheck_pyannote.py
Differences of a few tenths of a point against results/snapshot.json are the 10 ms frame
grid and collar edge handling of clinical_diarization/score.py, in either direction."""
import json, os, sys
from pathlib import Path
from pyannote.core import Annotation, Segment
from pyannote.metrics.diarization import DiarizationErrorRate

ROOT = Path(__file__).resolve().parents[1]
snapshot = json.loads((ROOT / "results/snapshot.json").read_text())
cases = [r["case"] for r in json.loads((ROOT / "data/manifest.json").read_text())["recordings"]]


def annotation(path: Path) -> Annotation:
    ann = Annotation()
    for s in json.loads(path.read_text())["segments"]:
        if s["end"] > s["start"]:
            ann[Segment(s["start"], s["end"])] = s["speaker"]
    return ann


references = {c: annotation(ROOT / f"data/references/full_recordings/{c}.json") for c in cases}
print(f"{'row':32} {'pyannote c=0':>13} {'snapshot':>9} {'pyannote c=0.5':>15} {'snapshot':>9}")
worst = 0.0
for model in snapshot["models"]:
    panel = model.get("full_recordings") or {}

    def der(collar_key: str):
        block = panel.get(collar_key) or {}
        block = block.get("aggregate") if isinstance(block.get("aggregate"), dict) else block
        return block.get("der")

    if der("0") is None or not (ROOT / f"data/hypotheses/{model['key']}/full_recordings").exists():
        continue  # aggregate-only rows (private outputs) cannot be cross-checked publicly
    scores = []
    for collar in (0.0, 0.5):
        metric = DiarizationErrorRate(collar=collar, skip_overlap=False)
        for c in cases:
            hyp = ROOT / f"data/hypotheses/{model['key']}/full_recordings/{c}.json"
            if hyp.exists():
                metric(references[c], annotation(hyp))
        scores.append(abs(metric))
    s0, s25 = der("0"), der("0.25")
    worst = max(worst, abs(scores[0] - s0), abs(scores[1] - s25))
    print(f"{model['key']:32} {100*scores[0]:12.3f}% {100*s0:8.3f}% {100*scores[1]:14.3f}% {100*s25:8.3f}%")
print(f"largest absolute difference: {100*worst:.3f} points")
sys.exit(0 if worst < 0.005 else 1)
