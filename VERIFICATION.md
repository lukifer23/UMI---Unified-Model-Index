# UMI v0.3.3 verification record

Verified on 2026-08-14 from `main` on macOS with Python 3.14.3 against the Python 3.11+
project contract.

## Commands and outcomes

| Check | Outcome |
|---|---|
| `uv sync --frozen --extra dev --no-editable --reinstall-package unified-model-index` | passed; installed UMI 0.3.3 as a wheel from the committed lock |
| `uv run --no-sync python -m scripts.build_v03_pilot` | passed; rebuilt all raw and processed pilot artifacts offline |
| schema equality test against `umi.schema_export.rendered_schemas()` | passed; committed machine-readable schemas remain current |
| `PYTHONPATH=. uv run --no-sync pytest` | 94 passed; 93% combined `umi`/`analysis` coverage |
| `PYTHONPATH=. uv run --no-sync ruff check .` | passed |
| `PYTHONPATH=. uv run --no-sync mypy --strict umi analysis scripts` | passed, 48 source files |
| `umi sources validate` | passed |
| `umi crosswalk` and `umi overlap` | passed |
| `umi bundle validate --data-dir data/pilots/v0.3/raw` | passed; all scored records have exact source, crosswalk, signal, budget, revision, checksum, and capture-type bindings |
| all ten offline `umi ingest --source ...` commands | passed: AA, Epoch ECI, Epoch benchmarks, both Arena cohorts, DeepSWE, and four lab-release sources |
| all 27 scoring/reporting CLI flows | passed |
| `umi validate` | schema valid with zero errors; deliberately exited 1 because eight records are diagnostic-only and the pilot is not headline-ready |
| explicit Epoch/Arena network acquisition into a fresh temporary snapshot | passed with a checksum manifest; destination reuse remains fail-closed |

The normal `uv run` auto-sync path creates an editable installation. Python 3.14 ignores the
underscore-prefixed editable `.pth` emitted in this environment, so the verified workflow installs a
wheel with `--no-editable` and uses `--no-sync` for subsequent commands. This is documented in the
README rather than hidden as a local workaround.

## Acquisition reconciliation

- The newly acquired Epoch CSV is byte-identical to the frozen reviewed artifact at SHA-256
  `946538f24b2d16cbbccc54c554d86e5afb6d4b3f175bf9bdeae2af61869658b6`.
- The complete Epoch Benchmarking Hub archive is frozen at SHA-256
  `35a7c21ba7d535514ebcf9bbe7b8265d2e2da40ef6b1fa63fe49323c3395a18b`;
  four exact Max-effort rows each for GPQA Diamond, SciCode, and CritPt are adapted from the raw CSV
  members. Fable is rejected because fallback absence is not established for GPQA and is explicitly
  contradicted by fallback-composite labels for SciCode and CritPt.
- A later same-day acquisition produced a different ZIP-container hash because member timestamps
  changed, while all 77 extracted member names and bytes remained identical at semantic content hash
  `2b818e5b5ad1fcdba9f04616d6f1c7f71714a3d045967dbf09a7e13bf557f009`.
  Crosswalk revision binding uses this semantic content hash; registry integrity still checks the
  frozen container bytes.
- The pinned Arena agent Parquet has 47 rows; all 47 frozen reviewed rows match their upstream rows.
- The pinned Arena text-style-control Parquet has 10,262 rows; the deliberately bounded 100-row
  frozen review sample matches the first 100 upstream rows.
- The acquisition manifest records the caller-supplied snapshot ID, source URL, pinned Arena
  revision, artifact path, and SHA-256. Promotion into reviewed facts remains a separate offline
  step.

## Publication assertions

- Five exact canonical named-release configurations are visible, each with label-exact identity and
  first-party nominal pricing record.
- The configured capability matrix contains 65 model/benchmark cells: 17 ready scored, 3 diagnostic
  measurements, 1 diagnostic reference, 2 vendor-claim-only, and 42 missing.
- Every model-specific score is labeled `real evidence — model-specific partial estimate`; it is not
  a UMI rank. Four estimates use four of 13 capability families across two domains with 35.625%
  Capability coverage; Fable remains on one family at 16.5% because fallback absence is unverified.
- Every publishable rank and every `headline_overall` remains null.
- No workload category has ready all-model Efficiency evidence or successful-task Economics
  evidence. Nominal token tariffs are not converted into task costs without observed task usage and
  success records.
- Claude Fable 5 Max remains release-window-ineligible.
- Vendor claims are retained for claim calibration and gap diagnostics, never silently promoted to
  independent benchmark results.
- Diagnostic evidence and source metadata change the complete audit fingerprint without changing
  the scored audit fingerprint. Input order remains fingerprint-invariant.
- Arena Agent is diagnostic preference evidence with zero Capability weight. Its former positive
  allocation is redistributed to GDPval-AA v2 and tau3-Banking in their prior ratio; it cannot
  increase coverage, confidence, or source diversity.
- Epoch model release dates, evidence-as-of dates, and Arena leaderboard publication dates are
  serialized in separate fields; unknown evaluation dates remain null.

## Repository map

```text
analysis/                         ranking, gaps, correlations, Pareto, sensitivity
config/                           weights, families, eligibility, overlap policy
data/pilots/v0.3/raw/             generated typed pilot dataset and audit manifest
data/pilots/v0.3/processed/       deterministic provisional reports and gap matrix
data/sources/v0.3/                frozen artifacts, reviewed facts, exact crosswalk
schemas/                          generated JSON Schemas
scripts/build_v03_pilot.py        deterministic offline assembly
scripts/freeze_v03_open_sources.py explicit, immutable network acquisition
tests/test_v03_pilot.py           adversarial source/scoring/publication tests
umi/adapters/                     pure offline source adapters
umi/                              validation, readiness, scoring, fingerprinting, CLI
```

## Remaining evidence required for a real headline UMI

- exact-configuration, common-cohort capability results for the 42 missing cells, beginning with
  HLE, Terminal-Bench, ARC-AGI, and long-context/reliability evidence;
- arithmetic-mean attempt-level cost, input/output/cache-token use, wall time, turn count, and task
  success for the five models across at least three configured workload categories;
- independent replication or auditable raw result artifacts for vendor-only claims;
- fixed, versioned workload baskets for nominal-price scenario estimates, kept separate from
  observed successful-task Economics;
- empirical calibration or decorrelation of within-domain family budgets, a longitudinal reference
  cohort, and formal uncertainty propagation.

The next ingestion milestone should target one exact common capability cohort and one complete
five-model task-level workload cohort. The current gates must remain closed until those artifacts
exist; missing evidence must not be inferred, imputed, or reweighted away.
