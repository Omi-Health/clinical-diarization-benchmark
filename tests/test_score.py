import pytest
from clinical_diarization.score import score, aggregate


def seg(a, b, speaker="a"):
    return {"start": a, "end": b, "speaker": speaker}


def test_permutation_and_three_speakers():
    ref = [seg(0, 1, "a"), seg(1, 2, "b"), seg(2, 3, "c")]
    hyp = [seg(0, 1, "z"), seg(1, 2, "x"), seg(2, 3, "y")]
    assert score(ref, hyp, 3)["error_frames"] == 0


def test_miss_false_alarm_and_confusion_have_known_counts():
    ref = [seg(0, 2, "a"), seg(2, 4, "b")]
    hyp = [seg(0, 1, "x"), seg(1, 3, "y"), seg(4, 5, "x")]
    out = score(ref, hyp, 5)
    assert [out[k] for k in ["reference_frames", "miss_frames", "false_alarm_frames", "confusion_frames"]] == [400, 100, 100, 100]
    assert out["der"] == .75


def test_overlap_counts_speaker_time():
    out = score([seg(0, 1), seg(0, 1, "b")], [seg(0, 1, "x")], 1)
    assert out["reference_frames"] == 200
    assert out["miss_frames"] == 100
    assert out["der"] == .5


def test_collars_use_boundary_radius():
    ref, hyp = [seg(1, 3)], [seg(.8, 3.2)]
    assert score(ref, hyp, 4)["false_alarm_frames"] == 40
    out = score(ref, hyp, 4, .25)
    assert out["reference_frames"] == 150
    assert out["error_frames"] == 0


def test_silence_der_is_undefined_but_false_alarm_is_preserved():
    out = score([], [seg(0, 1)], 1)
    assert out["der"] is None and out["false_alarm_frames"] == 100


def test_micro_average_includes_silent_file_false_alarm():
    a = score([seg(0, 2)], [seg(0, 2)], 2)
    b = score([], [seg(0, 1)], 1)
    assert aggregate([a, b])["der"] == .5


def test_duplicate_segments_do_not_double_count_same_speaker():
    out = score([seg(0, 1)], [seg(0, 1), seg(0, 1)], 1)
    assert out["der"] == 0


def test_clipping():
    assert score([seg(0, 1)], [seg(-5, 5)], 1)["der"] == 0


def test_split_scoring_can_hide_identity_switches():
    ref = [seg(0, 1, "a"), seg(1, 2, "b"), seg(2, 3, "a"), seg(3, 4, "b")]
    hyp = [seg(0, 1, "x"), seg(1, 2, "y"), seg(2, 3, "y"), seg(3, 4, "x")]
    assert score(ref, hyp, 4)["der"] == .5
    assert score(ref[:2], hyp[:2], 2)["der"] == 0
    r2 = [seg(s["start"] - 2, s["end"] - 2, s["speaker"]) for s in ref[2:]]
    h2 = [seg(s["start"] - 2, s["end"] - 2, s["speaker"]) for s in hyp[2:]]
    assert score(r2, h2, 2)["der"] == 0


@pytest.mark.parametrize("bad", [seg(2, 1), seg(float("nan"), 1), seg(0, float("inf")), seg(0, 1, "")])
def test_invalid_segments(bad):
    with pytest.raises(ValueError):
        score([], [bad], 2)


@pytest.mark.parametrize("duration,collar", [(0, 0), (-1, 0), (1, -1), (float("inf"), 0)])
def test_invalid_horizon(duration, collar):
    with pytest.raises(ValueError):
        score([], [], duration, collar)
