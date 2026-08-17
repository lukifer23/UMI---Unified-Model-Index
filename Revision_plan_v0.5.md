# UMI v0.5 Governed Public

## Repository Hardening, Score Validation, Uncertainty, and Model Expansion

Executed on `main`. This is the specification that was implemented.

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
