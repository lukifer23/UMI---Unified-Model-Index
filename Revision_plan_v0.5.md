# UMI v0.5 Governed Public

## Repository Hardening, Score Validation, Uncertainty, and Model Expansion

Executed on `feat/umi-v05-governed-public`. This is the specification that was implemented.

### Hard constraints retained

- No paid evaluations.
- No invented data.
- No imputation of missing WeirdML or incomplete DeepSWE cost.
- v0.3 and v0.4 artifacts stay frozen.
- v0.4 five-pilot `umi_public` numbers must reproduce exactly.

### Hardening

- SHA-256 freeze of v0.4 `model-scores.json`, `common-core.json`, and `rejected-evidence.json`.
- Separate `config/editions/v0.5/` policy. Formula and weights unchanged.

### Score validation

- `umi/public_validate.py` reloads the zip, checks every published raw, checks the weighted sum,
  rebuilds the fingerprint, and compares the five Max pilots to frozen v0.4.
- `umi edition --edition v0.5 audit` fails closed on mismatch.

### Uncertainty

- 2048-draw Monte Carlo using published stderr or 95% CI half-width.
- Frozen headline panel statistics.
- Partial intervals: SciCode, CritPt, tokens, steps, and WeirdML cost stay at the point.
- Family ablation is diagnostic.

### Model expansion

- Score every frozen configuration with the complete ten-series common core.
- Result: five Max pilots plus Gemini 3.6 Flash high and GPT-5.4 xhigh.
- Exact effort identities. Not Max substitutes.

### Named candidate audits

- Audit Grok 4.5 High and Gemini 3.1 Pro Preview against the same ten-series gate.
- Do not invent scores. Missing series → `insufficient_common_support` diagnostic certificate.
- Keep the Access high-effort suffix panel. Do not admit unsuffixed WeirdML cost.

Result: neither candidate is headline-eligible. Grok misses WeirdML accuracy and cost.
Gemini misses the suffix-panel cost row (unsuffixed cost 1.36 exists and is excluded).

### Precise blocker report

When exact public evidence is unavailable, emit `blocker-report.json` with missing series,
affected model, required identity, sources, URLs, fail reason, and resolving evidence.
Also package source concentration, edition manifest, pairwise overlaps, and family ablation
without inventing data.

## 1.5 Commit in coherent phases

Commit each phase separately. Do not squash unrelated work. Do not rewrite history,
force-push, or implement on `main`. Suggested messages and the commits that fulfilled
them:

| Phase | Suggested commit | SHA | Branch |
|---|---|---|---|
| 1. Freeze, validate, expand | `Add UMI Public v0.5 Governed: freeze, validate, uncertainty, expand` | `40ffb7b` | `main` (already published) |
| 2. Certificate and overlap ranks | `Add governed Public index certificate, zip checksum, and overlap ranks` | `75f6cbc` | `main` (already published) |
| 3. Dashboard packaging | `Wire dashboard to uncertainty sidecars and finish Public index packaging` | `f4cc49b` | `main` (already published) |
| 4. Named-candidate audits | `Audit Grok 4.5 High and Gemini 3.1 Pro Preview as diagnostic-only` | `4896e6e` | `feat/umi-v05-governed-public` |
| 5. Blocker report and remaining packaging | `Emit a precise v0.5 blocker report and remaining packaging` | `de709d1` | `feat/umi-v05-governed-public` |
| 6. Phase map | `Record v0.5 coherent commit phases` | `0ac6a38` | `feat/umi-v05-governed-public` |
| 7. Baseline audit | `Add v0.5 baseline audit` | `6ffcbcb` | `feat/umi-v05-governed-public` |
| 8. Weight sensitivity | `Add diagnostic Public weight-sensitivity hypotheses` | `e4f7db4` | `feat/umi-v05-governed-public` |
| 9. Implementation report | `Complete the v0.5 implementation-report checklist` | `9dfa44e` | `feat/umi-v05-governed-public` |

Phases 1–3 stay on `main`. Later phases are separate commits on `feat/umi-v05-governed-public`.
History is not rewritten.

## Suggested commit sequence

```text
Freeze and classify the v0.4 experimental score release
Add governed public scoring bundle and typed evidence contracts
Unify v0.5 policy configuration and eliminate hardcoded scoring specs
Harden deployable-system identity and source crosswalks
Add UMI Public v0.5 Governed: freeze, validate, uncertainty, expand
Add governed Public index certificate, zip checksum, and overlap ranks
Wire dashboard to uncertainty sidecars and finish Public index packaging
Audit Grok 4.5 High and Gemini 3.1 Pro Preview as diagnostic-only
Emit a precise v0.5 blocker report and remaining packaging
Record v0.5 coherent commit phases
Add v0.5 baseline audit
Add diagnostic Public weight-sensitivity hypotheses
Complete the v0.5 implementation-report checklist
```

Fulfilled as `40ffb7b`, `75f6cbc`, `f4cc49b` on `main`, then `4896e6e`, `de709d1`, `0ac6a38`, `6ffcbcb`, `e4f7db4`, `9dfa44e` on `feat/umi-v05-governed-public`.
