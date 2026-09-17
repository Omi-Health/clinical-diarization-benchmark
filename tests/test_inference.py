import json
from pathlib import Path
import wave

import numpy as np
import pytest

from inference.processing import normalize_max_speakers, parse_native, probability_segments, stitch_windows
from inference.run import windowed_inference, configure


def test_stitch_matches_swapped_speakers_and_cuts_overlap():
    windows = [
        [dict(start_ms=0, end_ms=900, speaker='a'), dict(start_ms=900, end_ms=1200, speaker='b')],
        [dict(start_ms=0, end_ms=100, speaker='z'), dict(start_ms=100, end_ms=1200, speaker='y')],
    ]
    out = stitch_windows(windows, [0, 800], 400)
    assert out == [dict(start_ms=0, end_ms=900, speaker='spk_0'), dict(start_ms=900, end_ms=2000, speaker='spk_1')]


def test_fold_preserves_extra_activity_instead_of_dropping_it():
    rows = [dict(start=0, end=4, speaker='a'), dict(start=4, end=7, speaker='b'), dict(start=7, end=8, speaker='c')]
    assert normalize_max_speakers(rows, 2)[-1] == dict(start=7, end=8, speaker='spk_1')


def test_probability_decoder_strict_threshold_gap_and_drop():
    probs = np.zeros((12, 3))
    probs[:, 0] = .9
    probs[:8, 1] = .9
    probs[3:5, 1] = 0
    probs[10:, 2] = .9
    probs[8, 1] = .5  # Equality is inactive.
    settings = dict(frame_stride_ms=10, params=dict(onset=.5, offset=.5, pad_onset=0,
        pad_offset=0, min_duration_off=.03, constraint='drop'))
    segments = probability_segments(probs, settings, .12)
    assert segments == [dict(start=0, end=.12, speaker='speaker_0'), dict(start=0, end=.08, speaker='speaker_1')]
    with pytest.raises(ValueError):
        probability_segments(np.full((2, 2), np.nan), settings, .02)


def test_window_requests_use_correct_audio_offsets(tmp_path):
    samples = np.arange(28, dtype=np.int16)
    audio = tmp_path/'audio.wav'
    with wave.open(str(audio), 'wb') as f:
        f.setparams((1, 2, 10, 0, 'NONE', 'not compressed'))
        f.writeframes(samples.tobytes())
    received = []
    class Model:
        def diarize(self, **kwargs):
            with wave.open(kwargs['audio']) as f:
                received.append(np.frombuffer(f.readframes(f.getnframes()), dtype=np.int16).tolist())
            return [['0 1 speaker_0']]
    windowed_inference(Model(), audio, 2, .5)
    assert received == [samples[:20].tolist(), samples[15:].tolist()]


def test_native_parser_keeps_legacy_millisecond_truncation():
    assert parse_native([['0.1239 0.4569 arbitrary']], legacy_ms=True) == [
        dict(start_ms=123, end_ms=456, speaker='spk_0')]
    assert parse_native([['0.1239 0.4569 arbitrary']])[0]['start'] == .1239


def test_geometry_is_validated_and_no_private_preset_is_shipped():
    class Modules:
        chunk_len = 1
    class Model:
        streaming_mode = True
        sortformer_modules = Modules()
        def _check_streaming_parameters(self):
            self.checked = True
    model = Model()
    assert configure(model, dict(streaming_mode=True, geometry=dict(chunk_len=6))) == dict(chunk_len=6)
    assert model.checked
    with pytest.raises(ValueError):
        configure(model, dict(streaming_mode=False))
    configs = Path(__file__).resolve().parents[1]/'inference/configs'
    assert {p.stem for p in configs.glob('*.json')} == {'sortformer1', 'sortformer21', 'sortformer21_low_unpaced'}
