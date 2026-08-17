# IMPLEMENTATION_REPORT_V04

1. **Starting commit:** `3634f7f2ce9c93a64767c5656dbdca00531a0ba4`
2. **Ending commit:** (this branch tip after the public-scoring commit)
3. **Branch:** `feat/umi-v0.4-public`
4. **Architecture:** Separate UMI Public edition beside frozen v0.3. Public formula is 0.55 Capability + 0.25 Operational Efficiency + 0.20 Access Economics. Controlled billed Economics is unchanged.
5. **Added:** `umi/edition.py`, `umi/feasibility.py`, `umi/identity.py`, `umi/eligibility.py`, `umi/public.py`, `scripts/build_v04_public.py`, `config/editions/v0.4/*`, `docs/editions/v0.4/*`, `data/editions/v0.4/processed/*`, tests for freeze/feasibility/identity/public.
6. **Changed:** `umi/cli.py` (`umi edition validate|score --edition v0.4`).
7. **Accepted sources:** Epoch DeepSWE v1.1 mini-swe-agent rows (Pass@1, mean output tokens, mean agent steps).
8. **Rejected sources:** LiveBench extract (no five pilots); Epoch HLE/GPQA/SciCode/CritPt (incomplete five-set); AA and CursorBench five-row extracts (anchor n=5); Fable DeepSWE cost (432/436); composites/ECI.
9. **Five system identities:** `claude-opus-5-max` single_model_service; `claude-fable-5-max` fallback_composite_service; `gpt-5.6-sol-max` single_model_service; `kimi-k3-max` and `glm-5.2-max` open_weight_deployment (Max / GLM xhigh mapping retained).
10. **Common-core manifest:** empty required series. Only DeepSWE qualifies; six domains cannot be filled.
11. **Anchor strategy:** robust-z vs Epoch DeepSWE 50-config panel, logit for pass@1, log-invert for tokens/steps, no percentile fallback.
12. **Weights:** as specified in `config/editions/v0.4/weights.yaml`.
13. **Source concentration:** DeepSWE/Datacurve would dominate if used as the only filled families; families.yaml is diversified so the *policy* is feasible, but evidence is not.
14–17. **Headline scores:** all `umi_public = null` (`insufficient_common_support`). DeepSWE-normalized **Capability** and **Operational Efficiency** (tokens+steps) exist for all five and are written to `data/editions/v0.4/processed/model-scores.json`. Access Economics is null (no all-five complete 8+ cost series).
18–21. Intervals, rank ranges, source ablation, and 10k bootstrap are not published for a null headline. Deterministic component points are in `model-scores.json`.
22. **Limitations:** Public evidence cannot yet fill every required domain/subcomponent without inventing anchors or mixing harnesses. Access Economics is not provider billing.
23–24. Verification: `uv run pytest tests/test_public_v04.py tests/test_feasibility.py tests/test_identity_v04.py tests/test_v03_legacy_freeze.py`; `python -m scripts.build_v04_public`; `umi edition score --edition v0.4`. Full-suite record follows later commits.
25. **No paid requests.**
26. **No API keys required.**
27. **v0.3 artifacts** remain the golden SHA-256 set in `tests/test_v03_legacy_freeze.py`.
