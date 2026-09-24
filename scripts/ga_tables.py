"""Headline automatic-count tables; constrained and alternative rows are in the full configuration tables."""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
GA = json.loads((ROOT/'results/ga-20260924/snapshot.json').read_text())
OLD = {m['key']:m for m in json.loads((ROOT/'results/snapshot.json').read_text())['models']}
TIMING = json.loads((ROOT/'results/community1_timing.json').read_text())['models']
SPEED = json.loads((ROOT/'results/best_settings_receipt.json').read_text())['speed']
PAIRED = {m['key']:m for m in json.loads((ROOT/'results/speaker_policy_snapshot.json').read_text())['models']}


def fresh(arm, view, panel='full_recordings', collar='0.25'):
    return GA['arms'][arm]['views'][view][panel][collar]['aggregate']


def seconds(arm, view):
    speed = GA['arms'][arm]['speed']
    return speed.get('combined_median_s', {}).get(view, speed['median_s'])


def count(a):
    return f"{round(a['speaker_count_accuracy']*a['records'])}/{a['records']}"


def batch_rows(panel='full_recordings'):
    rows=[]
    for arm, name in [('ga_off_bf16','Nemotron 3 Diarization'),('v1_whole_bf16','Sortformer v1, whole-file BF16'),('v21_off_fp32','Sortformer v2.1, FP32')]:
        rows.append((name,fresh(arm,'model_card',panel),f"{seconds(arm,'model_card'):.3f} s/file · L4"))
    for key, name, speed in [('precision3','Pyannote Precision-3 API',f"{SPEED['precision3']['median_s_per_file']:.1f} s/file · API round trip"),('vibe_original','VibeVoice-ASR','123 s/file · joint ASR + diarization server')]:
        rows.append((name,OLD[key][panel]['0.25']['aggregate'],speed))
    rows.append(('Pyannote Community-1',PAIRED['community1']['policies']['automatic'][panel]['0.25']['aggregate'],f"{TIMING['community1']['median_s']:.3f} s/file · L4"))
    if panel=='common_scoring_intervals':
        rows.append(('Meta Muse Voice Transcribe',OLD['muse'][panel]['0.25']['aggregate'],'92 s/request · API round trip'))
    return sorted(rows,key=lambda r:r[1]['der'])


def comparison_lines(heading_level=3, panel='full_recordings'):
    h='#'*heading_level
    lines=[h+' Batch: automatic speaker counts','',
           'Same 15 whole recordings. No supplied speaker count or forced two-speaker reassignment. NVIDIA models ran locally on one L4; hosted APIs were measured through their public endpoints.','',
           '| Model | DER ↓ (±250 ms) | Correct speaker count ↑ | Measured time ↓ |',
           '|---|---:|---:|---|']
    for name,a,timing in batch_rows(panel):
        lines.append(f"| {name} | {a['der']*100:.3f}% | {count(a)} | {timing} |")
    lines+=['','Local L4 processing and hosted API round trips have different timing scopes. Standalone model results do not represent Omi’s production service. Muse was tested in separate chunks: its result is in the shared-interval table in the full results. Precision-2 known-two and windowed/folded Sortformer runs are in the full configuration tables. Measurement dates per row are in the [measurement record](results/RESULTS.md#measurement-record).','',
            h+' Batch: Omi runtime, automatic speaker counts','',
            '| Model | Baseline → Omi DER (±250 ms) | Change | Correct counts, before → after | Seconds/file, before → after | Speedup |',
            '|---|---:|---:|---:|---:|---:|']
    for name,base,runtime in [('Nemotron 3 Diarization','ga_off_bf16','ga_omi_graph'),('Sortformer v2.1','v21_off_fp32','v21_omi_tf32')]:
        b,a=fresh(base,'model_card',panel),fresh(runtime,'omi_automatic',panel)
        bt,at=seconds(base,'model_card'),seconds(runtime,'omi_automatic')
        lines.append(f"| {name} | {100*b['der']:.3f}% → {100*a['der']:.3f}% | {100*(a['der']-b['der']):+.3f} pp | {count(b)} → {count(a)} | {bt:.3f} → {at:.3f} | {bt/at:.2f}× |")
    b=PAIRED['community1']['policies']['automatic'][panel]['0.25']['aggregate']
    a=OLD['community1_omi_runtime_auto'][panel]['0.25']['aggregate']
    bt,at=TIMING['community1']['median_s'],TIMING['community1_omi_runtime_auto']['median_s']
    lines.append(f"| Pyannote Community-1 | {100*b['der']:.3f}% → {100*a['der']:.3f}% | {100*(a['der']-b['der']):+.3f} pp | {count(b)} → {count(a)} | {bt:.3f} → {at:.3f} | {bt/at:.2f}× |")
    lines+=['','Same model weights with Omi’s proprietary runtime; no retraining. Nemotron 3 Diarization and Sortformer runtime outputs are private; Community-1 runtime outputs are public. Strict DER can worsen while collared DER improves; both scores remain in the full results.','',
            h+' Streaming: automatic speaker counts','',
            '| Model / configuration | Output | DER ↓ (±250 ms) | Correct speaker count ↑ | Measured time ↓ |',
            '|---|---|---:|---:|---|']
    live=[]
    for key,name in [('pyannote_live','Pyannote live API'),('vibe_15b_paced','VibeVoice 1.5B'),('vibe_7b_paced','VibeVoice 7B')]:
        a=OLD[key][panel]['0.25']['aggregate'];live.append((name,'Delivered · paced',a,'Latency not measured'))
    for arm,name in [('ga_live_graph','Nemotron 3 Diarization + Omi'),('v21_live_tf32','Sortformer v2.1 + Omi')]:
        a=fresh(arm,'delivered_causal',panel);live.append((name,'Delivered · unpaced',a,f"{seconds(arm,'delivered_causal'):.3f} s/file · L4"))
    for name,kind,a,timing in sorted(live,key=lambda r:r[2]['der']):
        lines.append(f"| {name} | {kind} | {a['der']*100:.3f}% | {count(a)} | {timing} |")
    for arm,name in [('ga_stream_bf16','Nemotron 3 Diarization, native preset'),('v21_stream_fp32','Sortformer v2.1, native preset')]:
        a=fresh(arm,'native',panel)
        lines.append(f"| {name} | Retrospective · unpaced | {a['der']*100:.3f}% | {count(a)} | {seconds(arm,'model_card'):.3f} s/file · L4 |")
    lines+=['','Unpaced seconds/file measure processing throughput, not user-facing latency or concurrent-stream capacity. Native presets score the completed-file timeline; Omi live rows reconstruct delivered revisions. Sortformer v1 is offline-only.']
    return lines


def detail_lines():
    lines=['## Shared intervals, including Muse','','The same 20 intervals cover all 15 sources. Whole-file systems retain full-file context; Muse used separate requests. Correct counts below refer to intervals, not whole recordings.','',
           '| Model | DER ↓ (±250 ms) | Correct interval counts | Measured time |',
           '|---|---:|---:|---|']
    for name,a,timing in batch_rows('common_scoring_intervals'):
        lines.append(f"| {name} | {a['der']*100:.3f}% | {count(a)} | {timing} |")
    lines+=['','## Nemotron 3 and Sortformer L4 run: full scoring details','','Every tested view is retained. `known2` forces at most two labels after inference; `top2` drops extra channels. Those are supplementary processing experiments, not automatic model results. Windowed v1 count errors include stitching artifacts. Omi outputs are aggregate-only; baseline outputs can be rescored.','',
            '| Run | Output view | Whole DER zero | Whole DER ±250 ms | Common DER zero | Common DER ±250 ms | Whole count accuracy |',
            '|---|---|---:|---:|---:|---:|---:|']
    for arm,body in GA['arms'].items():
        for view,panels in body['views'].items():
            vals=[f"{100*panels[p][c]['aggregate']['der']:.3f}%" for p in ['full_recordings','common_scoring_intervals'] for c in ['0','0.25']]
            constrained='known2' in view or 'top2' in view
            counts='constrained' if constrained else count(panels['full_recordings']['0']['aggregate'])
            if arm.startswith('v1_') and 'whole' not in arm and not constrained:counts='window stitching'
            lines.append('| '+' | '.join([arm,view,*vals,counts])+' |')
    lines+=['','## Additional fixed two-speaker recipes','','These use complete-file speaker durations. They are not native known-speaker parameters or causal live results. All alternatives are in [the L4 run snapshot](ga-20260924/snapshot.json).','',
            '| Run | Processing order | DER ±250 ms |','|---|---|---:|']
    for family,items in GA['supplemental'].items():
        for arm,v in items.items():
            lines.append(f"| {arm} | {family} | {100*v['panels']['full_recordings']['0.25']['aggregate']['der']:.3f}% |")
    return lines

MEASUREMENT_RECORD=[
 ('Nemotron 3 Diarization, Sortformer v1 and v2.1 (headline rows, Omi runtime rows, streaming presets)','24 September 2026','one NVIDIA L4 (g6.2xlarge, Frankfurt), released Nemotron 3 checkpoint pinned by revision and SHA-256'),
 ('Sortformer configuration study (FP32/BF16, folded and automatic)','18 September 2026','one NVIDIA L4, public `inference/run.py`'),
 ('Pyannote Precision-3 API (automatic and known-two)','21 September 2026','hosted API, sequential requests'),
 ('Pyannote Precision-2 API (known-two)','29 August 2026','hosted API, sequential requests'),
 ('Pyannote Community-1 (automatic baseline and Omi runtime)','21–22 September 2026','NVIDIA L4; per-file timing in community1_timing.json'),
 ('Pyannote Community-1 (known-two baseline)','7 September 2026 (accuracy), 18 September 2026 (timing)','NVIDIA L4, Pyannote.audio 4.0.7'),
 ('Sortformer v2.1 supplementary Omi known-two batch','7 September 2026','production L4 measurement'),
 ('Sortformer Omi supplementary windowed/retrospective recipes','22 September 2026','NVIDIA L4'),
 ('Meta Muse Voice Transcribe','15 September 2026','hosted API, 20 requests'),
 ('VibeVoice-ASR (batch)','15 September 2026','local vLLM server, joint ASR + diarization'),
 ('Pyannote live API; VibeVoice streaming 1.5B and 7B (paced and unpaced)','before 17 September 2026','outputs frozen when the repository was first published; exact run dates were not recorded'),
]


def measurement_record_lines():
    lines=['## Measurement record','','Every row is a measurement made on the date shown; rows are not re-measured when others are added.','',
           '| Rows | Measured | Where |','|---|---|---|']
    for rows,date,where in MEASUREMENT_RECORD: lines.append(f'| {rows} | {date} | {where} |')
    return lines
