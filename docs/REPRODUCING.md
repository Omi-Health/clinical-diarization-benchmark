# Reproducing and extending the benchmark

## Quick Start

Python 3.10+; CPU only. No model weights, API keys or GPU needed to rescore the included outputs. Install [Git LFS](https://git-lfs.com/) to download the audio.

```bash
git lfs install
git clone https://github.com/Omi-Health/clinical-diarization-benchmark.git
cd clinical-diarization-benchmark
git lfs pull

python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
pytest -q
python scripts/verify_audio.py
python scripts/verify_snapshot.py
python scripts/render_results.py
```

The audio verifier checks all 15 WAV hashes, formats and durations against the frozen manifest. The score verifier recomputes **810 recording/interval/collar scores** for the public baseline outputs and checks their integer error counts against the snapshot. For Model X it checks aggregate arithmetic only. It also checks the hashes of the exported timing data and numeric results. The renderer updates both this README's tables and the detailed results page from the same snapshot.

For scoring only, clone with `GIT_LFS_SKIP_SMUDGE=1 git clone ...` and omit `git lfs pull` and `verify_audio.py`; the saved outputs can be rescored without downloading audio. CI checks LFS pointer hashes and expected sizes without downloading the WAVs on each run.

Score your own output with the same reference:

```bash
python -m clinical_diarization.score \
  --reference data/references/full_recordings/day1_consultation03.json \
  --hypothesis data/hypotheses/precision2/full_recordings/day1_consultation03.json \
  --duration 542.299 --collar-radius 0.25
```

Input JSON uses seconds and arbitrary speaker labels:

```json
{"segments": [{"start": 1.2, "end": 3.4, "speaker": "speaker_0"}]}
```

## Project Structure

```text
clinical-diarization-benchmark/
├── clinical_diarization/
│   └── score.py              # 10 ms, overlap-inclusive DER scorer and CLI
├── data/
│   ├── manifest.json         # Frozen recording IDs, audio hashes and intervals
│   ├── raw_audio/            # Exact 15 mixed WAVs, stored with Git LFS
│   ├── references/           # Speaker/timestamp references, no transcript text
│   ├── hypotheses/           # Named baselines' normalized speaker/timestamp outputs
│   └── ATTRIBUTION.md        # PriMock57 attribution and data licensing
├── results/
│   ├── RESULTS.md            # Detailed comparison, generated from the snapshot
│   ├── snapshot.json         # Scores and per-case counts; Model X aggregates only
│   └── file_hashes.json      # Exported data integrity checks
├── scripts/
│   ├── verify_snapshot.py    # Rescore included outputs and verify counts/hashes
│   ├── verify_audio.py       # Verify WAV hashes, formats and durations
│   └── render_results.py     # Update both README and detailed results tables
├── docs/METHODOLOGY.md
└── tests/
```

## Public vs Private Contents

This release reproduces **scoring from saved outputs**, rather than rerunning every model. Original inference runners, weights and live API access are not bundled. Model X additionally withholds its outputs. [Methodology](../docs/METHODOLOGY.md) explains the reference preparation, legacy normalization and remaining limits.

The public scoring workflow needs only the files in this repository. Model X's private review package is stored separately and is not required to verify any named baseline.

## Dataset

The reference timing is derived from [PriMock57](https://github.com/babylonhealth/primock57) and refined using VAD. These are simulated consultations; the annotations are not a new hand-verified clinical ground truth. The exact mixed WAVs used for scoring are included under `data/raw_audio/`; the original separate doctor/patient tracks remain available upstream. See [data attribution](../data/ATTRIBUTION.md) and the [CC BY 4.0 data licence](../data/LICENSE.md).

This benchmark uses **15 frozen consultations (2.4152 audio hours)**. The [Medical STT benchmark](https://github.com/Omi-Health/medical-STT-eval) uses a different evaluation subset and transcription metrics. DER measures speaker timing and attribution, whereas WER measures transcript errors; the percentages are not interchangeable.

## Adding a New Comparison

Corrections and reproducible comparisons are welcome through issues or pull requests. Include your inference configuration, speaker-count policy, timestamp source and the same scoring settings.

Use the frozen case list and audio hashes, export speaker/timestamp segments in the JSON format above, then score at both collar settings. Keep automatic and constrained speaker-count policies explicit. Include normalized outputs and per-case counts so others can check your aggregate result. Changes to the numeric snapshot or data also need updated file hashes and regenerated tables.

