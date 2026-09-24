"""Permutation-invariant DER, with overlap and silence false alarms retained."""
import argparse
import json
import math
from pathlib import Path

import numpy as np
from scipy.optimize import linear_sum_assignment

FRAME_S = 0.01
COUNTS = ("reference_frames", "miss_frames", "false_alarm_frames", "confusion_frames", "error_frames")


def validate_segments(segments):
    result = []
    for segment in segments:
        start, end = float(segment["start"]), float(segment["end"])
        speaker = segment["speaker"]
        if not math.isfinite(start) or not math.isfinite(end) or end < start:
            raise ValueError("Segment boundaries must be finite and end >= start")
        if not isinstance(speaker, str) or not speaker.strip():
            raise ValueError("Every speech segment needs a nonempty string speaker label")
        result.append({"start": start, "end": end, "speaker": speaker})
    return result


def score(reference, hypothesis, duration_s, collar_radius_s=0.0):
    """Score one recording; boundaries are seconds, labels are arbitrary strings.

    Segments are half-open [start, end). Activity is clipped to the recording.
    Collars exclude time around every supplied reference segment boundary.
    No speaker cap, merging, VAD mask or silence trimming is applied here.
    """
    if not math.isfinite(duration_s) or duration_s <= 0:
        raise ValueError("duration_s must be finite and positive")
    if not math.isfinite(collar_radius_s) or collar_radius_s < 0:
        raise ValueError("collar_radius_s must be finite and nonnegative")
    reference, hypothesis = validate_segments(reference), validate_segments(hypothesis)
    times = (np.arange(int(duration_s / FRAME_S)) + 0.5) * FRAME_S
    valid = np.ones(len(times), dtype=bool)

    def activity(segments, is_reference):
        labels = sorted({s["speaker"] for s in segments
                         if min(duration_s, s["end"]) > max(0, s["start"])})
        indices = {label: i for i, label in enumerate(labels)}
        matrix = np.zeros((len(times), len(labels)), dtype=bool)
        for s in segments:
            start, end = max(0, s["start"]), min(duration_s, s["end"])
            if end <= start:
                continue
            matrix[:, indices[s["speaker"]]] |= (times >= start) & (times < end)
            if is_reference and collar_radius_s:
                valid[:] &= ((abs(times - s["start"]) >= collar_radius_s)
                             & (abs(times - s["end"]) >= collar_radius_s))
        return matrix, labels

    ref, ref_labels = activity(reference, True)
    hyp, hyp_labels = activity(hypothesis, False)
    ref, hyp = ref[valid], hyp[valid]
    overlap = ref.astype(np.int64).T @ hyp.astype(np.int64)
    ri, hi = linear_sum_assignment(-overlap)
    correct = sum(int(overlap[r, h]) for r, h in zip(ri, hi))
    nr, nh = ref.sum(axis=1), hyp.sum(axis=1)
    denominator = int(nr.sum())
    miss = int(np.maximum(nr - nh, 0).sum())
    false_alarm = int(np.maximum(nh - nr, 0).sum())
    confusion = int(np.minimum(nr, nh).sum()) - correct
    counts = dict(reference_frames=denominator, miss_frames=miss,
                  false_alarm_frames=false_alarm, confusion_frames=confusion,
                  error_frames=miss + false_alarm + confusion)
    return {**counts, "der": counts["error_frames"] / denominator if denominator else None,
            "audio_s": duration_s, "ref_speaker_count": len(ref_labels),
            "hyp_speaker_count": len(hyp_labels),
            "speaker_count_correct": len(ref_labels) == len(hyp_labels),
            "mapping": {hyp_labels[h]: ref_labels[r] for r, h in zip(ri, hi)}}


def aggregate(rows):
    """Micro-average counts; do not average per-recording DER percentages."""
    counts = {key: sum(row[key] for row in rows) for key in COUNTS}
    den = counts["reference_frames"]
    return {**counts, "records": len(rows),
            "der": counts["error_frames"] / den if den else None}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--hypothesis", type=Path, required=True)
    parser.add_argument("--duration", type=float, required=True)
    parser.add_argument("--collar-radius", type=float, default=0.0)
    args = parser.parse_args()
    result = score(json.loads(args.reference.read_text())["segments"],
                   json.loads(args.hypothesis.read_text())["segments"],
                   args.duration, args.collar_radius)
    print(json.dumps(result, indent=2, allow_nan=False))


if __name__ == "__main__":
    main()
