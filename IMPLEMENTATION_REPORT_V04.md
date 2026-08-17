# IMPLEMENTATION_REPORT_V04

1. **Starting commit:** `3634f7f2ce9c93a64767c5656dbdca00531a0ba4`
2. **Ending commit:** (this `main` tip after the Public scoring commit)
3. **Branch:** `main` only. The earlier `feat/umi-v0.4-public` work was fast-forwarded and deleted.
4. **Architecture:** Separate UMI Public edition beside frozen v0.3. Public formula is 0.55 Capability + 0.25 Operational Efficiency + 0.20 Access Economics. Controlled billed Economics is unchanged.
5. **Added:** `umi/edition.py`, `umi/feasibility.py`, `umi/identity.py`, `umi/eligibility.py`, `umi/public.py`, `scripts/build_v04_public.py`, `config/editions/v0.4/*`, `docs/editions/v0.4/*`, `data/editions/v0.4/processed/*`, tests for freeze/feasibility/identity/public.
6. **Changed:** `umi/cli.py` (`umi edition validate|score --edition v0.4`); METHODOLOGY, README, PILOT_REPORT, VERIFICATION.
7. **Accepted sources:** Epoch chess, DeepSWE v1.1 mini-swe-agent Pass@1 / tokens / steps, AA SciCode, WeirdML accuracy, Epoch GPQA, OTIS Mock AIME, CritPt, WeirdML high-effort cost.
8. **Rejected / diagnostic sources:** LiveBench (no five pilots); HLE extract (no five `_max`); SimpleQA (no Fable `_max`); Epoch CursorBench extract (no Kimi `_max`); AA and CursorBench five-row extracts (anchor n=5); Fable DeepSWE cost (432/436); composites/ECI; official five-card tariffs.
9. **Five system identities:** `claude-opus-5-max` single_model_service; `claude-fable-5-max` fallback_composite_service; `gpt-5.6-sol-max` single_model_service; `kimi-k3-max` and `glm-5.2-max` open_weight_deployment (Max / GLM xhigh mapping retained).
10. **Common-core manifest:** ten required series, all five entity IDs, every panel n≥8.
11. **Anchor strategy:** robust-z after logit or `-log(x+1)`, winsor ±3, Φ map, no percentile fallback. Access uses the WeirdML high-effort suffix panel (n=50) so cheap historical completions cannot collapse the cost scale.
12. **Weights:** Capability 0.15 / 0.40 / 0.25 / 0.20; OpEff 0.60 / 0.40; Access 1.00 WeirdML cost; overall 0.55 / 0.25 / 0.20.
13. **Source concentration:** Epoch 0.35 of Capability (chess + math). DataCurve 0.22 and Artificial Analysis 0.18 of Capability. WeirdML 0.25. OpEff and Access are single-origin; the cap applies only when a component has two or more orgs.
14–17. **Headline scores:** all five `umi_public` published in `data/editions/v0.4/processed/model-scores.json`. Rank: Sol 66.27, Kimi 59.69, Opus 55.51, Fable 54.43, GLM 54.20.
18–21. Intervals and 10k bootstrap are unpublished (point extracts, no attempt residuals). Deterministic component points and `scored_data_fingerprint` are in `model-scores.json`. Presentation-only charts in `public-dashboard.html` consume that JSON: rank bars, stacked weighted contributions, grouped unweighted components, and a Capability series heatmap. `umi edition --edition v0.4 dashboard` does not rescore.
22. **Limitations:** Public evidence does not fill context reliability, language/instruction, service latency, or billed Economics. Access is source-reported WeirdML cost. Fable is the composite product.
23–24. Verification: recorded in `VERIFICATION.md` after the full suite.
25. **No paid requests.**
26. **No API keys required.**
27. **v0.3 artifacts** remain the golden SHA-256 set in `tests/test_v03_legacy_freeze.py`.
