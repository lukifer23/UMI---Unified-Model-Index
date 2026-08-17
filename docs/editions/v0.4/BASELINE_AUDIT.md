# UMI v0.4 baseline audit

Recorded on `feat/umi-v0.4-public` before any v0.4 scoring change.

## Repository

| Field | Value |
|---|---|
| Starting commit | `3634f7f2ce9c93a64767c5656dbdca00531a0ba4` |
| Starting title | Publish Capability certificate as first ranking; record open-ledger hunt |
| Branch | `feat/umi-v0.4-public` |
| Package | `0.3.16` |
| Engine | `umi-engine-v0.3.13` |
| Formula | `umi-methodology-v0.3.15` |
| Normalization | `umi-normalization-v0.3.4` |
| Uncommitted user work | none besides empty untracked `Revision_plan_v0.4.md` |

## Frozen v0.3 artifact SHA-256

| Path | SHA-256 |
|---|---|
| `data/pilots/v0.3/processed/comparison-certificate-three-model.json` | `2a790575e37ecaaeeb3a5d9fd8b98453bdac7e911f0cec9a7d4be6d33c830f10` |
| `data/pilots/v0.3/processed/model-specific-partial-estimates.json` | `094db06a5da2f3a70cb6bcc79b19b89670aea82b194c52c4ae78f4584441b496` |
| `data/pilots/v0.3/processed/common-evidence-three-model-comparison.json` | `6e08fa2a78eb5ea0f07f1063c7779ffdcf5a5101d2d7b23ad327a71db404b001` |
| `data/pilots/v0.3/processed/common-evidence-five-model-comparison.json` | `dc491e4bed73d5e5b2dbbc3b96f973ee3524b87912c9e731f27c74b59a7be73b` |
| `data/pilots/v0.3/raw/audit.yaml` | `c2f196976753957b30f53fd26ef3553222e2c1e61736d55d557d079db33ba0de` |

`scored_audit_fingerprint` in `audit.yaml`: `377191db5686a265d1ebe3868a6488e69a4dd48f3abb4909680823724a202fbb`.

## What this edition must not change

v0.3 processed artifacts, `headline_overall` nulls, Capability certificate bytes, and the OpenRouter controlled runner remain the legacy product. UMI Public is a separate edition.

## Verification at audit time

| Check | Result |
|---|---|
| `uv run pytest --cov-fail-under=90` | 171 passed; 93.33% coverage |
| Paid OpenRouter / live execute | not run |

Ruff and mypy for new v0.4 modules are recorded in later phase commits.
