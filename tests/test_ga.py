"""Fresh numbers must be traceable to public predictions and immutable timing evidence."""
from scripts.verify_ga import verify


def test_ga_public_evidence_recomputes():
    assert verify() == 7000
