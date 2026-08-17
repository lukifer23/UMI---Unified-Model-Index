# IMPLEMENTATION_REPORT_V05

1. **Starting commit:** `e76e68a`
2. **Branch:** `main` only.
3. **Hardening:** v0.4 processed artifacts frozen in `tests/test_v04_legacy_freeze.py`.
4. **Validation:** `umi/public_validate.py` reloads the Epoch zip, checks raw values, weighted sums, rebuilt fingerprints, and exact v0.4 reproduction for the five Max pilots.
5. **Uncertainty:** 2048-draw source-interval Monte Carlo plus family ablation. Partial intervals only.
6. **Expansion:** +2 complete common-core systems (`gemini-3.6-flash-high`, `gpt-5.4-2026-03-05-xhigh`). Four `_max` near-misses remain unpublished (no WeirdML).
7. **Five-pilot reproduction:** Sol 66.265839, Kimi 59.690663, Opus 55.510021, Fable 54.429636, GLM 54.202703.
8. **No paid requests. No API keys. No v0.3 or v0.4 rewrite.**
