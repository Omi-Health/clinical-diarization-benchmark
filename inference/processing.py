"""Extracted benchmark stitching, speaker normalization and probability decoding.

No production identity resolver or model-specific private settings are included.
"""
from dataclasses import dataclass
import numpy as np

_MAX_SORTFORMER_SPEAKERS = 4

def stitch_windows(
    window_segments: list[list[dict]],
    window_starts_ms: list[int],
    overlap_ms: int,
) -> list[dict]:
    """Merge per-window diarization outputs into one globally-labelled list.

    Segments in each window carry window-relative times and local speaker
    labels (spk_0..spk_3). For each consecutive window pair, local speakers
    seen in the overlap region are mapped to the previous window's global
    label with maximum time-overlap there; unseen locals get fresh global
    ids. The seam is cut mid-overlap: earlier window owns audio before the
    cut, later window after (segments clipped at the cut).

    Pure function — unit-testable without NeMo/GPU.
    """
    merged: list[dict] = []
    next_global = 0

    for w_idx, (segs, w_start) in enumerate(zip(window_segments, window_starts_ms)):
        # Absolute times for this window's segments.
        abs_segs = [
            {**s, "start_ms": s["start_ms"] + w_start, "end_ms": s["end_ms"] + w_start}
            for s in segs
        ]
        if w_idx == 0:
            mapping: dict[str, str] = {}
            for s in abs_segs:
                if s["speaker"] not in mapping:
                    mapping[s["speaker"]] = f"spk_{next_global}"
                    next_global += 1
                s["speaker"] = mapping[s["speaker"]]
            merged.extend(abs_segs)
            continue

        ov_start = w_start
        ov_end = w_start + overlap_ms
        cut = (ov_start + ov_end) // 2

        # Overlap-region time per (local speaker -> global speaker) pair.
        votes: dict[tuple[str, str], int] = {}
        for s in abs_segs:
            lo, hi = max(s["start_ms"], ov_start), min(s["end_ms"], ov_end)
            if hi <= lo:
                continue
            for m in merged:
                mlo, mhi = max(m["start_ms"], lo), min(m["end_ms"], hi)
                if mhi > mlo:
                    key = (s["speaker"], m["speaker"])
                    votes[key] = votes.get(key, 0) + (mhi - mlo)

        mapping = {}
        for (local, global_), t in sorted(votes.items(), key=lambda kv: -kv[1]):
            if local not in mapping and global_ not in mapping.values():
                mapping[local] = global_

        # Cut the seam: previous windows own < cut, this window owns >= cut.
        merged = [m for m in merged if m["start_ms"] < cut]
        for m in merged:
            if m["end_ms"] > cut:
                m["end_ms"] = cut

        for s in abs_segs:
            if s["end_ms"] <= cut:
                continue
            if s["start_ms"] < cut:
                s["start_ms"] = cut
            if s["speaker"] not in mapping:
                if next_global < _MAX_SORTFORMER_SPEAKERS:
                    mapping[s["speaker"]] = f"spk_{next_global}"
                    next_global += 1
                else:
                    # Cap reached: fold into the most-voted existing global.
                    fallback = max(votes.items(), key=lambda kv: kv[1])[0][1] if votes else "spk_0"
                    mapping[s["speaker"]] = fallback
            s["speaker"] = mapping[s["speaker"]]
            merged.append(s)

    # Coalesce adjacent same-speaker segments (seams produce splits).
    merged.sort(key=lambda s: s["start_ms"])
    out: list[dict] = []
    for s in merged:
        if out and out[-1]["speaker"] == s["speaker"] and s["start_ms"] - out[-1]["end_ms"] <= 250:
            out[-1]["end_ms"] = max(out[-1]["end_ms"], s["end_ms"])
        else:
            out.append(s)
    return out

def hyp_segment_values(item: dict) -> tuple[float, float, str]:
    start = item.get("start_ms")
    end = item.get("end_ms")
    if start is not None and end is not None:
        return float(start) / 1000.0, float(end) / 1000.0, str(item.get("speaker", "unknown"))
    return float(item.get("start", item.get("start_s", 0))), float(item.get("end", item.get("end_s", 0))), str(item.get("speaker", item.get("label", "unknown")))

def normalize_max_speakers(items: list[dict], max_speakers: int) -> list[dict]:
    durations: dict[str, float] = {}
    for item in items:
        start, end, speaker = hyp_segment_values(item)
        durations[speaker] = durations.get(speaker, 0.0) + max(0.0, end - start)
    keep = [speaker for speaker, _ in sorted(durations.items(), key=lambda row: -row[1])[:max_speakers]]
    mapping = {speaker: f"spk_{index}" for index, speaker in enumerate(keep)}
    fallback = f"spk_{max(0, max_speakers - 1)}"
    normalized = []
    for item in items:
        start, end, speaker = hyp_segment_values(item)
        normalized.append({"start": start, "end": end, "speaker": mapping.get(speaker, fallback)})
    return normalized

@dataclass(frozen=True)
class Params:
    onset: float
    offset: float
    pad_onset: float
    pad_offset: float
    min_duration_off: float
    constraint: str = "fold"

def binarize(sequence: np.ndarray, params: Params) -> np.ndarray:
    active = np.zeros(sequence.shape[0], dtype=bool)
    if params.onset != params.offset:
        raise ValueError("the bounded sweep requires equal onset/offset thresholds")
    speech_frames = np.flatnonzero(sequence > params.onset)
    if not len(speech_frames):
        return active
    cuts = np.flatnonzero(np.diff(speech_frames) > 1) + 1
    groups = np.split(speech_frames, cuts)
    spans = [(int(group[0]), int(group[-1]) + 1) for group in groups]

    pad_left = round(params.pad_onset * 100)
    pad_right = round(params.pad_offset * 100)
    padded = [(max(0, left - pad_left), min(len(sequence), right + pad_right)) for left, right in spans]
    merged = [padded[0]]
    max_gap = round(params.min_duration_off * 100)
    for left, right in padded[1:]:
        prev_left, prev_right = merged[-1]
        if left - prev_right < max_gap:
            merged[-1] = (prev_left, max(prev_right, right))
        else:
            merged.append((left, right))
    for left, right in merged:
        active[left:right] = True
    return active

def select_two(hyp: np.ndarray, fold_extras: bool) -> np.ndarray:
    order = np.argsort(-hyp.sum(axis=0))
    selected = hyp[:, order[:2]].copy()
    if fold_extras and hyp.shape[1] > 2:
        selected[:, 1] |= hyp[:, order[2:]].any(axis=1)
    return selected


def probability_segments(probs, settings, duration_s):
    stride = settings["frame_stride_ms"]
    if not isinstance(stride, int) or stride <= 0 or stride % 10:
        raise ValueError("frame_stride_ms must be a positive multiple of 10")
    if probs.ndim != 2 or not np.isfinite(probs).all() or (probs < 0).any() or (probs > 1).any():
        raise ValueError("Expected finite frame-by-speaker probabilities in [0, 1]")
    probs = np.repeat(probs, stride // 10, axis=0)[:int(np.ceil(duration_s * 100))]
    params = Params(**settings["params"])
    if params.constraint not in {"fold", "drop"}:
        raise ValueError("constraint must be fold or drop")
    raw = np.column_stack([binarize(probs[:, i], params) for i in range(probs.shape[1])])
    hyp = select_two(raw, fold_extras=params.constraint == "fold")
    segments = []
    for i in range(hyp.shape[1]):
        edges = np.diff(np.r_[False, hyp[:, i], False].astype(int))
        for a, b in zip(np.flatnonzero(edges == 1), np.flatnonzero(edges == -1)):
            segments.append(dict(start=int(a)/100, end=int(b)/100, speaker=f"speaker_{i}"))
    return segments


def parse_native(annotations, legacy_ms=False):
    if not annotations:
        return []
    rows, names = [], {}
    for entry in annotations[0]:
        values = entry.split() if isinstance(entry, str) else entry
        if len(values) != 3:
            raise ValueError("Expected start, end, speaker")
        a, b, speaker = float(values[0]), float(values[1]), str(values[2])
        if not np.isfinite([a, b]).all() or b < a:
            raise ValueError("Invalid native segment boundaries")
        if legacy_ms:
            names.setdefault(speaker, f"spk_{len(names)}")
            rows.append(dict(start_ms=int(a*1000), end_ms=int(b*1000), speaker=names[speaker]))
        else:
            rows.append(dict(start=a, end=b, speaker=speaker))
    return rows
