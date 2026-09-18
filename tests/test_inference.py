import json
from pathlib import Path
import wave

import numpy as np
import pytest

from inference.processing import normalize_max_speakers, parse_native, probability_segments, stitch_windows
from inference.run import windowed_inference, configure, resolve_checkpoint


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


def test_geometry_is_validated_and_model_x_presets_are_ready():
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
    assert {p.stem for p in configs.glob('*.json')} == {'sortformer1', 'sortformer21', 'sortformer21_low_unpaced', 'model_x', 'model_x_streaming_unpaced'}

    for key in ['model_x', 'model_x_streaming_unpaced']:
        config = json.loads((configs / (key + '.json')).read_text())
        assert config['model_id'] == 'Model X'
        assert config['geometry']
        assert 'checkpoint_sha256' not in config and 'model_revision' not in config
    streaming = json.loads((configs/'model_x_streaming_unpaced.json').read_text())
    assert streaming['mode'] == 'native'
    assert 'postprocessing' not in streaming and 'fold_to' not in streaming


def test_model_name_alone_resolves_checkpoint_and_records_revision(tmp_path):
    from types import SimpleNamespace
    checkpoint = tmp_path/'downloaded.nemo'
    checkpoint.write_bytes(b'test checkpoint')
    calls = []
    class API:
        def model_info(self, model_id, revision):
            calls.append((model_id, revision))
            return SimpleNamespace(sha='resolved-revision', siblings=[
                SimpleNamespace(rfilename='README.md'), SimpleNamespace(rfilename='weights.nemo')])
    def download(**kwargs):
        calls.append(kwargs)
        return str(checkpoint)
    config = json.loads((Path(__file__).resolve().parents[1]/'inference/configs/model_x.json').read_text())
    config['model_id'] = 'example/diarization'
    path, digest, revision = resolve_checkpoint(config, api=API(), download=download)
    assert path == checkpoint and len(digest) == 64 and revision == 'resolved-revision'
    assert calls == [('example/diarization', 'main'),
        dict(repo_id='example/diarization', filename='weights.nemo', revision='resolved-revision')]


def test_placeholder_and_ambiguous_download_fail_without_guessing(tmp_path):
    from types import SimpleNamespace
    with pytest.raises(ValueError, match='Replace'):
        resolve_checkpoint(dict(model_id='Model X'))
    class API:
        def model_info(self, *args, **kwargs):
            return SimpleNamespace(sha='resolved', siblings=[SimpleNamespace(rfilename=f'{n}.nemo') for n in [1, 2]])
    with pytest.raises(ValueError, match='Expected one'):
        resolve_checkpoint(dict(model_id='example/diarization'), api=API(), download=lambda **kwargs: pytest.fail('Unexpected download'))
    checkpoint = tmp_path/'local.nemo'
    checkpoint.write_bytes(b'local')
    with pytest.raises(ValueError, match='hash mismatch'):
        resolve_checkpoint(dict(model_id='Model X', checkpoint_sha256='wrong'), checkpoint)
    assert resolve_checkpoint(dict(model_id='Model X'), checkpoint)[0] == checkpoint


def test_native_parser_preserves_extra_speakers_and_overlap():
    # The native path must not silently merge/drop a third speaker or overlap.
    rows = [['0.1 0.6 speaker_0', '0.1 0.6 speaker_1', '0.3 0.8 speaker_2']]
    parsed = parse_native(rows)
    assert len(parsed) == 3
    assert len({s['speaker'] for s in parsed}) == 3
    assert [s['start'] for s in parsed] == [.1, .1, .3]


def test_common_interval_clipping_retains_overlapping_speakers():
    from inference.score_run import clip
    segments = [dict(start=0, end=2, speaker='a'), dict(start=1, end=3, speaker='b'),
                dict(start=4, end=5, speaker='c')]
    assert clip(segments, 1.5, 1) == [dict(start=0, end=.5, speaker='a'), dict(start=0, end=1, speaker='b')]


def test_geometry_receipt_reports_native_effective_cache_period():
    class Modules:
        chunk_len = 340
        fifo_len = 40
        spkcache_update_period = 300
        def _check_streaming_parameters(self):
            pass
    class Model:
        streaming_mode = True
        sortformer_modules = Modules()
    model = Model()
    result = configure(model, dict(geometry=dict(chunk_len=340, fifo_len=40, spkcache_update_period=300)))
    assert result['spkcache_update_period'] == 340
    assert model.sortformer_modules.spkcache_update_period == 300


def test_score_run_scores_both_panels_and_collars(tmp_path, monkeypatch):
    import inference.score_run as scorer
    monkeypatch.setattr(scorer, 'ROOT', tmp_path)
    data = tmp_path/'data'
    data.mkdir()
    (data/'manifest.json').write_text(json.dumps(dict(
        recordings=[dict(case='a', audio_duration_s=1)],
        common_intervals=[dict(case='a_part', source_case='a', offset_s=0, duration_s=1)])))
    for panel, name in [('full_recordings', 'a'), ('common_scoring_intervals', 'a_part')]:
        d = data/'references'/panel
        d.mkdir(parents=True)
        (d/f'{name}.json').write_text(json.dumps(dict(segments=[dict(start=0, end=.8, speaker='r')])))
    out = tmp_path/'output/full_recordings'
    out.mkdir(parents=True)
    (out/'a.json').write_text(json.dumps(dict(segments=[dict(start=0, end=.4, speaker='h')])))
    result = scorer.score_run(out.parent)
    for panel in result.values():
        for block in panel.values():
            assert block['aggregate']['der'] == .5
            assert block['rows'][0]['audio_s'] == 1
            assert block['aggregate']['speaker_count_accuracy'] == 1
