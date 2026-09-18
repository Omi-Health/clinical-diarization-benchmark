import json
import pytest
pytest.importorskip('pyannote.metrics')
from pyannote.core import Segment
from scripts.crosscheck_pyannote import annotation


def test_simultaneous_identical_boundaries_keep_both_speakers(tmp_path):
    p = tmp_path/'segments.json'
    p.write_text(json.dumps(dict(segments=[dict(start=0, end=1, speaker=s) for s in ['a', 'b']])))
    ann = annotation(p)
    assert ann.get_labels(Segment(0, 1)) == {'a', 'b'}


def test_hypothesis_support_unions_same_speaker_without_losing_other(tmp_path):
    p = tmp_path/'segments.json'
    p.write_text(json.dumps(dict(segments=[dict(start=0, end=1, speaker='a'),
        dict(start=.5, end=2, speaker='a'), dict(start=0, end=1, speaker='b')])))
    ann = annotation(p).support()
    assert ann.label_duration('a') == 2
    assert ann.label_duration('b') == 1
