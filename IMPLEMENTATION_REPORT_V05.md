# IMPLEMENTATION_REPORT_V05

## Reviewed baseline versus current HEAD

The execution spec reviewed `9712b35f2c3fe162110c4c29e25101f2fe3a58f8`
(`Publish first five-model UMI Public scores from frozen Epoch extracts`).
Current `HEAD` is `f4cc49b5ef3e79f60d15cbc302596c97eed078a2`
(`Wire dashboard to uncertainty sidecars and finish Public index packaging`).
`main` moved. The checked-out tree is authoritative. No reset to `9712b35`.

Commits after the reviewed baseline:

| Commit | Title |
|---|---|
| `2dfb1e4` | Add Public methods write-up and presentation-only charts |
| `e76e68a` | Add grouped component bars and Capability heatmap to Public dashboard |
| `40ffb7b` | Add UMI Public v0.5 Governed: freeze, validate, uncertainty, expand |
| `75f6cbc` | Add governed Public index certificate, zip checksum, and overlap ranks |
| `f4cc49b` | Wire dashboard to uncertainty sidecars and finish Public index packaging |

That delta already added v0.5 scoring, zip validation, partial intervals, two extra
complete high-effort systems, a public-index certificate, and dashboard packaging.
Further spec work continues from this tree, not from `9712b35`.

1. **Starting commit for remaining spec work:** `f4cc49b`
2. **Branch:** `feat/umi-v05-governed-public`. Spec work is not implemented on `main`.
3. **Hardening:** v0.4 processed artifacts frozen in `tests/test_v04_legacy_freeze.py`.
4. **Validation:** `umi/public_validate.py` reloads the Epoch zip, checks raw values, weighted sums, rebuilt fingerprints, and exact v0.4 reproduction for the five Max pilots.
5. **Uncertainty:** 2048-draw source-interval Monte Carlo plus family ablation. Partial intervals only.
6. **Expansion:** +2 complete common-core systems (`gemini-3.6-flash-high`, `gpt-5.4-2026-03-05-xhigh`). Four `_max` near-misses remain unpublished (no WeirdML).
7. **Five-pilot reproduction:** Sol 66.265839, Kimi 59.690663, Opus 55.510021, Fable 54.429636, GLM 54.202703.
8. **Certificate:** `public-index-certificate.json` binds scores, zip checksum, license, intervals, and overlap pairs. Schema: `schemas/public-index-certificate.schema.json`.
9. **Named candidates:** Grok 4.5 High misses WeirdML accuracy and cost (8/10). Gemini 3.1 Pro Preview misses high-effort WeirdML cost (9/10; unsuffixed cost 1.36 is excluded by the Access suffix panel). Both emit diagnostic certificates with `umi_public: null`. Neither is added to identities or headline scores.
10. **v0.4 classification:** historical experimental point-score edition. It does not prove rank stability or independent validation. v0.5 is the governed public index.
11. **No paid requests. No API keys. No v0.3 or v0.4 rewrite.**
12. **Verification this turn:** 212 pytest passed; 92.48% coverage; ruff clean; mypy 69 files; v0.5 validate/audit/candidates/certificate/blockers smoked. v0.3/v0.4 goldens restored after pytest rewrite.
13. **Blocker report:** `docs/editions/v0.5/BLOCKER_REPORT.md` and `data/editions/v0.5/processed/blocker-report.json` list every unpublished identity and omitted construct with sources, URLs, and resolving evidence. No invented scores.
14. **Nonblocked packaging:** edition manifest, source concentration (Epoch Capability 0.35 at the cap), pairwise overlap export, and diagnostic family ablation.
15. **Commit phases (1.5):** `40ffb7b` freeze/validate/expand; `75f6cbc` certificate; `f4cc49b` dashboard packaging on `main`. `4896e6e` candidate audits; `de709d1` blocker report on `feat/umi-v05-governed-public`. No history rewrite.
