# Dataset attribution and licensing

Source dataset: **PriMock57: A Dataset of Primary Care Mock Consultations**, by Alex Papadopoulos Korfiatis, Francesco Moramarco, Radmila Sarac and Aleksandar Savkov (2022), released by Babylon Health.

- [Dataset repository](https://github.com/babylonhealth/primock57)
- [Paper and full author list](https://aclanthology.org/2022.acl-short.65/)
- [Upstream CC BY 4.0 license](https://github.com/babylonhealth/primock57/blob/main/LICENSE.md)
- [CC BY 4.0 terms](https://creativecommons.org/licenses/by/4.0/)

The source recordings are simulated doctor/patient consultations, not recordings of actual patient care.

Changes by Omi: a frozen 15-recording selection; conversation mixing and trimming; VAD intersection of source timing annotations; conversion to timestamp/speaker-only JSON; common-interval splitting; model-generated timestamp predictions and error scoring. The 15 mixed WAVs are included through Git LFS in `data/raw_audio/`; transcript text is not included.

The mixed audio, PriMock-derived timing annotations, normalized predictions and Omi's contributions to the benchmark data under `data/` and `results/` are shared under **CC BY 4.0**, as stated in [data/LICENSE.md](LICENSE.md). Preserve source attribution and describe any further changes. Third-party model names do not imply endorsement. This repository grants no license to model weights or vendor APIs.

The code outside these data directories is separately licensed under MIT.
