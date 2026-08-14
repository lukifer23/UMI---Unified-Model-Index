# UMI v0.3.1 verification record

Verified on 2026-08-14 from `main` on macOS with Python 3.14.3 against the Python 3.11+
project contract.

## Commands and outcomes

| Check | Outcome |
|---|---|
| `uv sync --frozen --extra dev --no-editable --reinstall-package unified-model-index` | passed; installed UMI 0.3.1 as a wheel from the committed lock |
| `uv run --no-sync python -m scripts.build_v03_pilot` | passed; rebuilt all raw and processed pilot artifacts offline |
| `uv run --no-sync python -m umi.schemas` | passed; regenerated the machine-readable schemas |
| `PYTHONPATH=. uv run --no-sync pytest --cov=umi --cov=analysis --cov-fail-under=90` | 88 passed; 93.19% combined `umi`/`analysis` coverage |
| `PYTHONPATH=. uv run --no-sync ruff check .` | passed |
| `PYTHONPATH=. uv run --no-sync mypy --strict umi analysis scripts` | passed, 46 source files |
| `umi sources validate` | passed |
| `umi crosswalk` and `umi overlap` | passed |
| `umi bundle validate --data-dir data/pilots/v0.3/raw` | passed; all scored records have exact source, crosswalk, signal, budget, revision, checksum, and capture-type bindings |
| all nine offline `umi ingest --source ...` commands | passed: AA, Epoch, both Arena cohorts, DeepSWE, and four lab-release sources |
| rank, estimates, both sensitivity paths, references, correlations, Pareto, both comparison cohorts, uncertainty, claims, and gaps | passed |
| `umi validate` | schema valid with zero errors; deliberately exited 1 because eight records are diagnostic-only and the pilot is not headline-ready |
| explicit Epoch/Arena network acquisition into a fresh temporary snapshot | passed with a checksum manifest; destination reuse remains fail-closed |

The normal `uv run` auto-sync path creates an editable installation. Python 3.14 ignores the
underscore-prefixed editable `.pth` emitted in this environment, so the verified workflow installs a
wheel with `--no-editable` and uses `--no-sync` for subsequent commands. This is documented in the
README rather than hidden as a local workaround.

## Acquisition reconciliation

- The newly acquired Epoch CSV is byte-identical to the frozen reviewed artifact at SHA-256
  `946538f24b2d16cbbccc54c554d86e5afb6d4b3f175bf9bdeae2af61869658b6`.
- The pinned Arena agent Parquet has 47 rows; all 47 frozen reviewed rows match their upstream rows.
- The pinned Arena text-style-control Parquet has 10,262 rows; the deliberately bounded 100-row
  frozen review sample matches the first 100 upstream rows.
- The acquisition manifest records the caller-supplied snapshot ID, source URL, pinned Arena
  revision, artifact path, and SHA-256. Promotion into reviewed facts remains a separate offline
  step.

## Publication assertions

- Five exact canonical configurations are visible, each with a verified release snapshot and
  first-party nominal pricing record.
- The configured capability matrix contains 65 model/benchmark cells: 5 ready scored, 3 diagnostic
  measurements, 9 diagnostic references, 2 vendor-claim-only, and 46 missing.
- Every model-specific score is labeled `real evidence — model-specific partial estimate`; it is not
  a UMI rank. The estimates use only one of 13 capability families and have 16.5% capability weight
  coverage.
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

- exact-configuration, common-cohort capability results for the 46 missing cells, beginning with
  HLE, Terminal-Bench, SciCode, GPQA Diamond/CritPt, ARC-AGI, and long-context/reliability evidence;
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
