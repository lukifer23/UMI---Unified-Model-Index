# UMI v0.5 baseline audit

Recorded on `feat/umi-v05-governed-public` against the reviewed baseline. No reset
to that baseline. Later phase commits implement remaining spec work.

## Repository

| Field | Value |
|---|---|
| Reviewed baseline | `9712b35f2c3fe162110c4c29e25101f2fe3a58f8` |
| Branch start / `main` at branch creation | `f4cc49b5ef3e79f60d15cbc302596c97eed078a2` |
| Branch | `feat/umi-v05-governed-public` |
| Package | `0.3.16` |
| Engine | `umi-engine-v0.3.13` |
| v0.4 formula | `umi-methodology-v0.4.0` |
| v0.5 formula | `umi-methodology-v0.5.0` |

## What this edition must not change

v0.3 processed artifacts, `headline_overall` nulls, and the Capability certificate stay
legacy. Frozen v0.4 `model-scores.json`, `common-core.json`, and `rejected-evidence.json`
stay the reproduction gate. Scoring remains offline. No API keys. No paid evaluations.

## Frozen v0.4 artifact SHA-256

See `tests/test_v04_legacy_freeze.py`.
