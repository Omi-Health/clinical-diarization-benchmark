"""Keep checkpoint versions, speaker policies and timing scopes visible."""
import importlib.util
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('render_results', ROOT/'scripts/render_results.py')
render = importlib.util.module_from_spec(spec)
spec.loader.exec_module(render)
SNAPSHOT = json.loads((ROOT/'results/snapshot.json').read_text())

def test_main_tables_use_automatic_counts_and_verified_ga():
    text = '\n'.join(render.comparison_lines(SNAPSHOT))
    for name in ['Precision-3', 'Sortformer v1', 'Sortformer v2.1', 'Nemotron 3', 'Community-1', 'VibeVoice']:
        assert name in text
    assert 'Pending' not in text
    assert 'DER zero' not in text
    assert '4.803%' in text and '3.174%' in text
    assert '3.157%' not in text  # Windowed, forced-two result stays supplementary.
    assert '2.13×' in text
    assert '14/15' in text


def test_live_vs_retrospective_is_explicit():
    text = '\n'.join(render.comparison_lines(SNAPSHOT)).split('## Streaming:')[1]
    causal = next(line for line in text.splitlines() if '| Nemotron' in line and '+ Omi' in line)
    assert '4.575%' in causal and 'Delivered · unpaced' in causal and '7.540 s/file' in causal
    retrospective = next(line for line in text.splitlines() if '| Nemotron' in line and 'native preset' in line)
    assert '4.971%' in retrospective and 'Retrospective' in retrospective


def test_rendering_preserves_numeric_snapshot_and_is_idempotent():
    path = ROOT/'results/snapshot.json';before = path.read_bytes()
    render.main();first = ((ROOT/'README.md').read_bytes(),(ROOT/'results/RESULTS.md').read_bytes())
    render.main()
    assert path.read_bytes() == before
    assert first == ((ROOT/'README.md').read_bytes(),(ROOT/'results/RESULTS.md').read_bytes())


def test_community1_timing_receipt_matches_automatic_score_policies():
    import statistics
    timing = json.loads((ROOT/'results/community1_timing.json').read_text())
    paired = json.loads((ROOT/'results/speaker_policy_snapshot.json').read_text())
    automatic = next(m for m in paired['models'] if m['key'] == 'community1')['policies']['automatic']['full_recordings']['0.25']
    runtime = next(m for m in SNAPSHOT['models'] if m['key'] == 'community1_omi_runtime_auto')['full_recordings']['0.25']
    for key, scores in [('community1', automatic), ('community1_omi_runtime_auto', runtime)]:
        measured = timing['models'][key]
        assert len(measured['rows']) == scores['aggregate']['records'] == 15
        assert statistics.median(r['total_s'] for r in measured['rows']) == measured['median_s']
        assert measured['correct_counts'] == sum(r['hyp_speakers'] == 2 for r in measured['rows'])
        by_case = {r['case']: r for r in scores['rows']}
        assert set(by_case) == {r['case'] for r in measured['rows']}
        for r in measured['rows']:
            assert r['hyp_speakers'] == by_case[r['case']]['hyp_speaker_count']
