# Clinical Diarization Benchmark

Evaluation framework for speaker diarization on medical conversation data: who spoke when.

Built by [Omi Health](https://omi.health) · [All research](https://omi.health/research) · [Medical STT benchmark](https://github.com/Omi-Health/medical-STT-eval)

## Benchmark Results

<!-- BENCHMARK:START -->

**Dataset**: PriMock57 (15 mock consultations, 2.4152 audio hours) | **Configurations**: 11 | **Updated**: 2026-09-17

**DER ↓** measures who-spoke-when errors; lower is better. Each recording has two reference speakers. Speaker-count policies differ, as shown below.

### Batch / offline

Ordered by **common-interval DER at ±250 ms**, lowest first. Speaker policies still differ.

| System | Speaker policy | Whole DER, zero | Whole DER, ±250 ms | Common DER, zero | Common DER, ±250 ms | Whole-file count accuracy |
|---|---|---:|---:|---:|---:|---:|
| pyannoteAI Precision-2 API | Known 2 | 11.004% | 2.823% | 10.986% | 2.824% | constrained |
| Sortformer v1, 180s windows | Folded to 2 after inference | 12.706% | 3.157% | 12.706% | 3.158% | constrained |
| Sortformer v2.1, whole-file | Folded to 2 after inference | 12.173% | 3.610% | 12.173% | 3.611% | constrained |
| Model X | Automatic | 12.589% | 4.786% | 12.589% | 4.787% | 80.0% |
| pyannoteAI Community-1, whole-file | Known 2; historical folding to 2 | 15.856% | 6.323% | 15.855% | 6.325% | constrained |
| VibeVoice-ASR, native batch | Automatic | 24.191% | 8.233% | 24.191% | 8.235% | 100.0% |
| Meta Muse Voice Transcribe | Automatic per request | 29.169%\* | 13.042%\* | 29.169% | 13.042% | 90.0%\* |

\* **Muse:** starred cells use the same **20 independently scored intervals** as its common-interval results, not whole-recording scores. Five recordings were split at the API's 10-minute limit; speaker-count accuracy is **18/20 intervals (90%)**. Speaker identity across chunk boundaries is not evaluated.

### Real-time-paced streaming

Ordered by **common-interval DER at ±250 ms**, lowest first. Speaker policies still differ.

| System | Speaker policy | Whole DER, zero | Whole DER, ±250 ms | Common DER, zero | Common DER, ±250 ms | Whole-file count accuracy |
|---|---|---:|---:|---:|---:|---:|
| VibeVoice streaming 1.5B, paced | Automatic | 32.947% | 17.210% | 32.947% | 17.215% | 100.0% |
| VibeVoice streaming 7B, paced | Automatic | 33.808% | 18.032% | 33.808% | 18.036% | 86.7% |

### Supplementary: streaming checkpoints run unpaced

Ordered by **common-interval DER at ±250 ms**, lowest first. Speaker policies still differ.

| System | Speaker policy | Whole DER, zero | Whole DER, ±250 ms | Common DER, zero | Common DER, ±250 ms | Whole-file count accuracy |
|---|---|---:|---:|---:|---:|---:|
| VibeVoice streaming 7B, unpaced | Automatic | 32.627% | 16.838% | 32.627% | 16.842% | 93.3% |
| VibeVoice streaming 1.5B, unpaced | Automatic | 32.669% | 16.952% | 32.669% | 16.956% | 100.0% |

<!-- BENCHMARK:END -->

**Reading the tables:**

- **±250 ms** is the exclusion radius around each reference boundary, equivalent to a pyannote total collar of **0.5 seconds**. Zero-collar scores are also shown.
- **Common intervals** use the same 20 scoring intervals for all systems. Muse required five recordings to be split at 600 seconds. Speaker matching restarts per interval; inference context still differs.
- **Constrained** speaker counts are not automatic-counting results. The historical two-speaker folding is already present in the published baseline outputs.
- **Model X** shares aggregate results only. Its identity, inference code, configuration and individual outputs remain private; its row cannot be independently reproduced from this repo.

Overlap and false alarms during silence are retained. References are frozen VAD-corrected PriMock timings. Speed is not ranked because hardware, APIs and the work performed differ across systems.

[Detailed results](results/RESULTS.md) · [Numeric snapshot](results/snapshot.json) · [Methodology](docs/METHODOLOGY.md)

**Omi's proprietary runtime performance is not included in these tables.** These are third-party model configurations evaluated by Omi; an evaluation of our own runtime will be published separately.

This is a comparison of saved system configurations. Some use a known two-speaker count or historical output folding; others infer the count automatically. Those differences are shown beside the scores. This small, repeatedly evaluated subset does not establish performance on new clinical audio or larger groups.

### Metrics Explained

| Metric | What it measures |
|---|---|
| **DER ↓** | Diarization Error Rate: missed speech + false alarm + speaker confusion, divided by reference speaker time |
| **Missed speech ↓** | Reference speaker activity with no corresponding predicted activity |
| **False alarm ↓** | Excess predicted speaker activity, including speech predicted during silence |
| **Speaker confusion ↓** | Active speech assigned to the wrong speaker after optimal label matching |
| **Count accuracy ↑** | Fraction of whole recordings with the correct number of predicted speakers; reported for automatic-count runs |

Whole-recording scores use one speaker mapping per recording. Common-interval scores use a separate mapping per interval. Corpus DER sums integer error counts before dividing by total reference speaker time. Error components and counts are available in the [numeric snapshot](results/snapshot.json).

## What's Included

- An open, permutation-invariant DER scorer: 10 ms frames, overlap included, false alarms during silence retained.
- The exact 15 mixed benchmark WAVs (about 278 MB), stored with Git LFS under `data/raw_audio/`.
- Frozen reference timings, normalized baseline speaker/timestamp outputs and per-recording error counts. Transcript text is not included.
- Two collar settings: zero and **±250 ms around reference boundaries**.
- Full-recording and common-interval results, with explicit speaker-count policies.
- **Model X aggregate results only.** Its inference code, settings, identity and individual outputs are kept private. Its row cannot be independently reproduced from this repository.

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

The audio verifier checks all 15 WAV hashes, formats and durations against the frozen manifest. The score verifier recomputes **670 recording/interval/collar scores** for the public baseline outputs and checks their integer error counts against the snapshot. For Model X it checks aggregate arithmetic only. It also checks the hashes of the exported timing data and numeric results. The renderer updates both this README's tables and the detailed results page from the same snapshot.

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

This release reproduces **scoring from saved outputs**, rather than rerunning every model. Original inference runners, weights and live API access are not bundled. Model X additionally withholds its outputs. [Methodology](docs/METHODOLOGY.md) explains the reference preparation, legacy normalization and remaining limits.

The public scoring workflow needs only the files in this repository. Model X's private review package is stored separately and is not required to verify any named baseline.

## Dataset

The reference timing is derived from [PriMock57](https://github.com/babylonhealth/primock57) and refined using VAD. These are simulated consultations; the annotations are not a new hand-verified clinical ground truth. The exact mixed WAVs used for scoring are included under `data/raw_audio/`; the original separate doctor/patient tracks remain available upstream. See [data attribution](data/ATTRIBUTION.md) and the [CC BY 4.0 data licence](data/LICENSE.md).

This benchmark uses **15 frozen consultations (2.4152 audio hours)**. The [Medical STT benchmark](https://github.com/Omi-Health/medical-STT-eval) uses a different evaluation subset and transcription metrics. DER measures speaker timing and attribution, whereas WER measures transcript errors; the percentages are not interchangeable.

## Adding a New Comparison

Corrections and reproducible comparisons are welcome through issues or pull requests. Include your inference configuration, speaker-count policy, timestamp source and the same scoring settings.

Use the frozen case list and audio hashes, export speaker/timestamp segments in the JSON format above, then score at both collar settings. Keep automatic and constrained speaker-count policies explicit. Include normalized outputs and per-case counts so others can check your aggregate result. Changes to the numeric snapshot or data also need updated file hashes and regenerated tables.

## Related Benchmarks

- [Medical STT Benchmark](https://github.com/Omi-Health/medical-STT-eval): transcription, medical-term and drug-term accuracy.
- [Clinical SOAP Note Safety Benchmark](https://github.com/Omi-Health/medical-note-eval): generated-note quality and safety.

## Citation

```bibtex
@misc{omi_clinical_diarization_2026,
  title  = {Clinical Diarization Benchmark},
  author = {{Omi Health}},
  year   = {2026},
  url    = {https://github.com/Omi-Health/clinical-diarization-benchmark},
  note   = {15 frozen PriMock57 mock consultations; September 2026 snapshot}
}
```

Please also credit the [PriMock57 dataset authors](data/ATTRIBUTION.md).

## License

Code: [MIT](LICENSE). Audio, derived references, normalized predictions and benchmark data: [CC BY 4.0](data/LICENSE.md).

---

Built by **[Omi Health](https://omi.health)** — medical voice infrastructure.
