# Previous snapshot

These are the results before the September 18 reruns (the intermediate native-only BF16 table is superseded as well; see `docs/NATIVE_RERUN_DECOMPOSITION_20260918.md`). Sortformer outputs were folded to two speakers; Model X streaming used tuned decoding and retained the top two speakers. They are not the current native-model results.

The corresponding public outputs, references and documentation remain available at commit `b454b9d6bc106ddfac1f010b1e3565ce8fab67fa`. Historical presets are retained in `inference/configs/legacy/` for inspection. In particular, the historical v2.1 production-path row was not exactly reproduced by the extracted adapter; this archive does not claim otherwise.

The earlier attribution of the v2.1 discrepancy to an approximately 0.5 s merge was not established by the saved evidence. NeMo itself applies an effective cache-period clamp; this was not an adapter-only omission. The new native runs remove dependence on that historical runtime path.
