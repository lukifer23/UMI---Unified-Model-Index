# UMI v0.3 verification record

Verified on 2026-08-14 from `main` on Windows with Python 3.12 against the Python 3.11+ project
contract.

## Commands and outcomes

| Check | Outcome |
|---|---|
| `uv sync --frozen` | passed; installed UMI 0.3.0 from the committed lock |
| `uv sync --frozen --extra dev` | passed |
| `pytest -q` | 77 passed; 94% combined `umi`/`analysis` coverage |
| `ruff check .` | passed |
| `mypy --strict umi analysis scripts` | passed, 40 source files |
| schema generator plus `git diff --exit-code -- schemas` | passed; no schema drift |
| `umi sources validate` | passed |
| `umi crosswalk` and `umi overlap` | passed |
| all five `umi ingest --source ...` commands | passed offline |
| rank, both sensitivity commands, correlations, and Pareto | passed |

## Publication assertions

- Five exact canonical configurations are visible.
- Every model-specific row is labeled `real evidence — model-specific partial estimate`; it is not
  a rank. Any provisional ranks are emitted only by an explicit common-evidence comparison group.
- Every publishable rank is null.
- Every `headline_overall` is null.
- Efficiency and Economics remain unscored because captured DeepSWE summaries do not prove
  arithmetic-mean semantics and cover only coding.
- Claude Fable 5 Max remains release-window-ineligible.
- Diagnostic/rejected evidence changes the complete audit fingerprint without changing the scored
  fingerprint.

## Repository map

```text
analysis/                         ranking, correlations, Pareto, sensitivity
config/                           weights, families, eligibility, overlap policy
data/pilots/v0.3/raw/             generated typed pilot dataset and audit manifest
data/pilots/v0.3/processed/       deterministic provisional reports
data/sources/v0.3/                frozen artifacts, reviewed facts, exact crosswalk
schemas/                          generated JSON Schemas
scripts/build_v03_pilot.py        deterministic offline assembly
scripts/freeze_v03_open_sources.py explicit network acquisition for Epoch/Arena only
tests/test_v03_pilot.py           adversarial source/scoring/publication tests
umi/adapters/                     pure source adapters
umi/                              validation, readiness, scoring, fingerprinting, CLI
```

## Open methodology questions

- empirical calibration or decorrelation of within-domain family budgets;
- a fixed reference cohort or anchored longitudinal scale;
- formal propagation of source confidence intervals;
- arithmetic-mean, attempt-level resource evidence across multiple workload categories;
- cross-workload Economics aggregation and nominal-price workload baskets;
- calibrated source-quality weights and treatment of preference evidence.

## Recommended next ingestion task

For the same five exact configurations, freeze task-level HLE, GPQA Diamond/CritPt, and one
context/reliability family with dates, harnesses, task counts, and configuration evidence. Separately
obtain arithmetic-mean attempt-level cost/token/time records across at least three workload
categories. Preserve the current gates and union cohort; do not infer matches or reweight missing
workloads.
