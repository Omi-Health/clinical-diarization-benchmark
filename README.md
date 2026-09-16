# Clinical diarization benchmark

Who spoke when in a clinical conversation? A small, auditable comparison from [Omi — medical voice infrastructure](https://omi.health).

**15 frozen PriMock57 mock consultations · 2.4152 audio hours · two speakers per recording.**

Compare Sortformer v1 and v2.1, Community-1, Precision-2, Meta Muse, VibeVoice and an anonymized **Model X**. Batch, paced streaming and unpaced streaming-checkpoint runs are reported separately.

**[View the comparison →](results/RESULTS.md)**

This is a comparison of saved system configurations. Some use a known two-speaker count or historical output folding; others infer the count automatically. Those differences are shown beside the scores. This small, repeatedly evaluated subset does not establish performance on new clinical audio or larger groups.

## What's included

- An open, permutation-invariant DER scorer: 10 ms frames, overlap included, false alarms during silence retained.
- Frozen reference timings, normalized baseline speaker/timestamp outputs and per-recording error counts. No audio or transcript text.
- Two collar settings: zero and **±250 ms around reference boundaries**.
- Full-recording and common-interval results, with explicit speaker-count policies.
- **Model X aggregate results only.** Its inference code, settings, identity and individual outputs are kept private. Its row cannot be independently reproduced from this repository.

## Check the results

Python 3.10+; CPU only. No model weights, API keys or GPU needed to rescore the included outputs.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
pytest -q
python scripts/verify_snapshot.py
python scripts/render_results.py
```

The verifier recomputes **670 recording/interval/collar scores** for the public baseline outputs and checks their integer error counts against the snapshot. For Model X it checks aggregate arithmetic only. It also checks the hashes of the exported data and numeric results.

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

## Reproducibility and scope

This release reproduces **scoring from saved outputs**, rather than rerunning every model. Original inference runners, weights and live API access are not bundled. Model X additionally withholds its outputs. [Methodology](docs/METHODOLOGY.md) explains the reference preparation, legacy normalization and remaining limits.

The reference timing is derived from [PriMock57](https://github.com/babylonhealth/primock57) and refined using VAD. These are simulated consultations; the annotations are not a new hand-verified clinical ground truth. Audio remains with the upstream dataset. See [data attribution and licensing](data/ATTRIBUTION.md).

Corrections and reproducible comparisons are welcome through issues or pull requests. Include your inference configuration, speaker-count policy, timestamp source and the same scoring settings.

Code: [MIT](LICENSE). PriMock-derived timing annotations and benchmark data: [CC BY 4.0](data/ATTRIBUTION.md).
