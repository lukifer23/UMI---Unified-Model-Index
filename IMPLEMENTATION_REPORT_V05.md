# IMPLEMENTATION_REPORT_V05

## Current hardening branch (`feat/umi-v05-governed-public-2`)

Starting commit for this unique replacement branch: `4af92006c1ec8263d693d7b03bca5c345b582729`.
Reviewed spec baseline: `9712b35f2c3fe162110c4c29e25101f2fe3a58f8`.
`origin/main` at branch creation: `f4cc49b5ef3e79f60d15cbc302596c97eed078a2`.
Local checkout before fetch was stale at `976460f`. No reset. No history rewrite.

### Publication decision

v0.5 is **`provisional_public_score`**, not `certified_public_score`.

Reason codes from `decide_public_eligibility`:

- `source_concentration_failed` — Access 1.00 WeirdML; Operational Efficiency 1.00 DataCurve. The 0.35 cap has no single-source exemption.
- `construct_incomplete` — missing context reliability, language/instruction following, interactive latency, agentic task cost, and fixed tariff baskets.
- `success_adjustment_unavailable` — DeepSWE tokens/steps and WeirdML cost are unadjusted means.

CritPt concentration origin is now Artificial Analysis (evaluator/run executor). Epoch is the distributor only. Capability Epoch share is 0.30, under the cap.

### v0.4 freeze

Companion `data/editions/v0.4/processed/release-status.json` labels the release `experimental_point_score`. The five committed scores and fingerprint `e266af13…8e6d` are unchanged. Ranks remain point-estimate order only.

### Identity

`_source_effort` no longer infers Max/High/xhigh from suffixes. Blank row effort is unknown unless a reviewed crosswalk binds the exact `Model version`.

### Candidates

Unchanged diagnostic result: Grok 4.5 High 8/10 (missing WeirdML accuracy and cost); Gemini 3.1 Pro Preview 9/10 (missing high-effort WeirdML cost). `umi_public: null`. Grok 4.6 remains intake.

### Remaining work after the bundle/normalization slice

Success-adjusted OpEff, diversified Access, hierarchical attempt bootstrap, isolated-wheel
CI smoke, and rights-clear source expansion remain open. Missing public evidence is recorded
in `docs/editions/v0.5/BLOCKER_REPORT.md` rather than invented.

This slice made `score_public_bundle` the production scorer, added explicit fingerprinted
anchor members, applied v0.5-only log/IQR normalization, excluded the conflicting WeirdML
Qwen row by declared policy, and stopped claiming strict ranks.

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
15. **Commit phases (1.5):** suggested sequence is in `Revision_plan_v0.5.md`. On `main`: `40ffb7b`, `75f6cbc`, `f4cc49b`. On the feature branch: `4896e6e`, `de709d1`, `0ac6a38`, `6ffcbcb`, `e4f7db4`, `9dfa44e`. No history rewrite.

## Final checklist

1. **Starting commit:** `f4cc49b` (`main` at branch creation). Reviewed spec baseline `9712b35`.
2. **Ending commit:** this report's commit on `feat/umi-v05-governed-public`.
3. **Branch:** `feat/umi-v05-governed-public`. Not implemented on `main`.
4. **Architecture:** v0.5 governed Public edition beside frozen v0.3 and historical experimental v0.4. Formula remains 0.55/0.25/0.20. Validation, partial intervals, certificate, candidate audits, blocker report, and diagnostic sensitivity are separate from the scorer.
5. **Added:** `umi/public_candidates.py`, `umi/public_blockers.py`, `umi/public_governance.py`, `umi/public_sensitivity.py`, candidate/blocker/governance artifacts, `docs/editions/v0.5/BLOCKER_REPORT.md`, `docs/editions/v0.5/BASELINE_AUDIT.md`.
6. **Changed:** `umi/cli.py`, `umi/public.py`, `umi/public_validate.py`, `umi/schema_export.py`, METHODOLOGY, README, PILOT_REPORT, DATA_SCHEMA, VERIFICATION.
7. **Accepted sources:** same ten Epoch-zip series as v0.4, plus the two extra complete high-effort identities.
8. **Rejected / blocked:** Grok 4.5 High; Gemini 3.1 Pro Preview; Terra/Luna/Sonnet 5/Opus 4.8 Max; DeepSWE cost; context reliability; language/instruction; interactive latency; billed Economics; hierarchical bootstrap. See `BLOCKER_REPORT.md`.
9. **Scored identities:** five Max pilots plus `gemini-3.6-flash-high` and `gpt-5.4-2026-03-05-xhigh`.
10. **Common core:** ten series, coverage 1.0, every panel n≥8.
11. **Anchors:** robust-z after logit or `-log(x+1)`, winsor ±3, Φ. Access uses the high-effort suffix panel.
12. **Weights:** Capability 0.15/0.40/0.25/0.20; OpEff 0.60/0.40; Access 1.00; overall 0.55/0.25/0.20.
13. **Source concentration:** Epoch 0.35 of Capability (at the cap). DataCurve 0.22, AA 0.18, WeirdML 0.25. OpEff and Access are single-origin.
14–17. **Headline scores:** Sol 66.265839, Kimi 59.690663, GPT-5.4 xhigh 55.511377, Opus 55.510021, Gemini 3.6 Flash high 55.439997, Fable 54.429636, GLM 54.202703.
18–19. **Partial intervals and rank ranges:** Sol 1–1, Kimi 2–2, places 3–7 overlap. See `uncertainty.json`.
20. **Source ablation:** diagnostic family drops in `source-ablation.json`. Sol and Kimi stay 1–2.
21. **Weight sensitivity:** diagnostic named hypotheses. Sol and Kimi stay 1–2; places 3–7 move. Headline unchanged.
22. **Limitations:** no context/language/latency/billed Economics; intervals are partial; bootstrap unpublished.
23–24. **Verification:** last full suite 212 passed, 92.48% coverage, ruff clean, mypy 69 files. Later phases add targeted tests.
25. **No paid requests.**
26. **No API keys required.**
27. **v0.3 and frozen v0.4 goldens** remain the SHA-256 sets in the freeze tests.
