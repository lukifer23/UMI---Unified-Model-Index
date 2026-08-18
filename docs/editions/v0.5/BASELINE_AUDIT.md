# UMI Public v0.5 baseline audit

Recorded on branch `feat/umi-v05-governed-public-2` before further hardening.

## Commits

| Ref | SHA | Note |
|---|---|---|
| Local checkout before fetch | `976460fa04769db4eb9a389cc0101b6350659520` | Stale v0.3.15 tree; no public scorer |
| Spec-reviewed baseline | `9712b35f2c3fe162110c4c29e25101f2fe3a58f8` | First five-model UMI Public scores |
| `origin/main` | `f4cc49b5ef3e79f60d15cbc302596c97eed078a2` | First v0.5 packaging pass |
| Branch start | `4af92006c1ec8263d693d7b03bca5c345b582729` | Existing `feat/umi-v05-governed-public` tip |
| Unique replacement | `feat/umi-v05-governed-public-2` | This implementation branch |

No reset to `9712b35`. History was not rewritten.

## Frozen artifact SHA-256

| Path | SHA-256 |
|---|---|
| `data/editions/v0.4/processed/model-scores.json` | `0c4256c585966e63d9b67b2d5e64f23e62c17718bf1a7030d01f1e6a3786006c` |
| `data/editions/v0.4/processed/common-core.json` | `83c7819c5792798ce67b062ce70d6ab592d47d2733c0f4425e64ecdb9e0152dd` |
| `data/editions/v0.4/processed/rejected-evidence.json` | `aa04375010e6cd01c2c417f09374030b3a83e452b612762d2f033dcc75eb8d44` |
| `data/pilots/v0.3/processed/comparison-certificate-three-model.json` | `2a790575e37ecaaeeb3a5d9fd8b98453bdac7e911f0cec9a7d4be6d33c830f10` |
| `data/sources/v0.3/epoch-benchmark-data-2026-08-14.zip` | `35a7c21ba7d535514ebcf9bbe7b8265d2e2da40ef6b1fa63fe49323c3395a18b` |

v0.4 scored-data fingerprint in the committed JSON: `e266af13b966cf79cfc5086513ec35f60cf2194f896f41f4b332f60ac9788e6d`.

v0.4 five-model `umi_public` values match the spec to the committed decimals. Live rebuild on this host differs at floating-point ULPs (`math.erf`); the committed bytes remain the freeze. v0.5 fingerprints will use declared canonical digits.

## Pre-existing test failures on the feat tip

- `test_frozen_v04_processed_artifacts_are_byte_identical` — GOLDEN hashes stale vs current files
- `test_v04_scores_through_the_public_bundle_without_drift` — live fingerprint ULP drift
- `test_committed_candidate_audits_match_live` — rebuilt fingerprint ≠ stored payload

## P0 status at branch start

The feat tip added wrappers and candidate audits. It did **not** close P0-01 through P0-23. Production scoring still reads the Epoch ZIP through a repo-relative path, infers effort from suffixes, exempts single-source components from the 0.35 cap, attributes CritPt to Epoch, labels v0.5 `governed_public_index` / `published`, and hardcodes `publication_state: published`.

## Package metadata at branch start

```text
pyproject / umi.version: 0.3.16 / umi-engine-v0.3.13 / umi-methodology-v0.3.15
v0.5 edition.yaml: package 0.5.0 / engine v0.3.13 / methodology v0.5.0
```
