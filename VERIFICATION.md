# UMI v0.3.7 verification record

Verified on 2026-08-15 from `main` on macOS with Python 3.14.3 against the Python 3.11+
project contract.

## Commands and outcomes

| Check | Outcome |
|---|---|
| `uv sync --frozen --extra dev --no-editable --reinstall-package unified-model-index` | passed; installed UMI 0.3.7 as a wheel from the committed lock |
| `uv run --no-sync python -m scripts.build_v03_pilot` | passed; rebuilt all raw and processed pilot artifacts offline |
| schema equality test against `umi.schema_export.rendered_schemas()` | passed; committed machine-readable schemas remain current |
| `uv run pytest` | 112 passed |
| `uv run pytest --cov=umi --cov=analysis --cov=scripts --cov-report=term-missing --cov-fail-under=90` | 112 passed; 92.32% combined coverage |
| `PYTHONPATH=. uv run --no-sync ruff check .` | passed |
| `PYTHONPATH=. uv run --no-sync mypy --strict umi analysis scripts` | passed, 50 source files |
| `umi sources validate --strict` | passed; complete registry, crosswalk, licensing, attribution, diagnostic, pricing, and release-claim audit is valid |
| `umi crosswalk` and `umi overlap` | passed |
| `umi bundle validate --data-dir data/pilots/v0.3/raw` | passed; acceptance manifest admits 37 records and excludes 8 diagnostic records with 0 unready scored records |
| all thirteen offline `umi ingest --source ...` commands | passed: AA composite facts, AA HLE, AA GDPval, CursorBench, Epoch ECI, Epoch benchmarks, both Arena cohorts, DeepSWE, and four lab-release sources |
| documented validation, ingestion, scoring, comparison, analysis, and certificate CLI flows | passed with valid JSON output |
| five-model and three-model common-evidence comparisons | passed; Kimi DeepSWE remains 25.0 on the identical five-model panel, and every raw/normalized contribution carries panel and scale identity |
| joint comparison sensitivity | passed; 32 exhaustive five-model scenarios and 512 exhaustive three-model scenarios, with possible-rank and robust-dominance envelopes and no probability claims |
| `umi certificate` for Opus/Kimi/GLM | passed; seven common stable panels, 21 selected records, five exact artifact checksums, 512 joint scenarios, deterministic certificate fingerprint `40780e19…cbda4` |
| portable dashboard packaging | passed at 1440 px and 390 px; seven charts rendered, source dialog passed, no overflow, external-request, or browser-error failure |
| isolated Python 3.11 and Python 3.14 dashboard rebuild tests | passed; bounded presentation precision keeps canonical JSON and embedded HTML payloads compatible across interpreter versions |
| `uv build` plus fresh temporary-environment wheel install outside the checkout | passed on Python 3.14.3; `import umi`, `umi --help`, and the certificate smoke all passed with the same result fingerprint |
| `umi validate --data-dir tests/fixtures --config-dir tests/fixtures/config` | passed without a source registry; schema and selected scored inputs are valid |
| explicit Epoch/Arena network acquisition into a fresh temporary snapshot | passed with a checksum manifest; destination reuse remains fail-closed |

The normal `uv run` auto-sync path creates an editable installation. Python 3.14 ignores the
underscore-prefixed editable `.pth` emitted in this environment, so the verified workflow installs a
wheel with `--no-editable` and uses `--no-sync` for subsequent commands. This is documented in the
README rather than hidden as a local workaround.

GitHub Actions [run 31879575407](https://github.com/lukifer23/UMI---Unified-Model-Index/actions/runs/31879575407)
for UMI v0.3.7 commit `48af724` completed successfully. Linux 3.12 passed the full quality, schema,
governed validation, deterministic rebuild, CLI, and isolated-wheel gates. Linux 3.11 and 3.14 each
passed the test suite plus isolated-wheel import/help/comparison smokes. Windows 3.12 passed tests,
generic validation, governed bundle validation, strict source/checksum audit, deterministic rebuild
diff, and the three-model comparison smoke. These hosted results—not the local macOS run—establish
the recorded Linux and Windows compatibility claim. Two preceding runs exposed Python 3.11
float-representation drift in the portable dashboard; the final run proves the
presentation-boundary canonicalization fix across all four hosted jobs. GitHub emitted only Node 20
deprecation
annotations for `actions/checkout@v4` and `astral-sh/setup-uv@v6`; no UMI job failed.

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
- CursorBench 3.2 is retained as a facts-only artifact at SHA-256
  `19556c9ff6db835757a5668a65177e8e151759eda751ca6e627a7491e77e54bc`. Four exact Max rows
  score Capability. Fable is rejected because the retained identity review documents invisible
  Fable-to-Opus routing without run-level fallback proof. Cost/task, tokens/task, and steps/task are
  retained as non-scoring settings.
- GDPval-AA v2 is retained as a facts-only artifact at SHA-256
  `7c18c5ba6483bd4db4826bb45a25d8393b92e5cc4b788cf482f7d9f21808f9cb`. Four exact Max-effort
  Elo rows and their source-declared 95% intervals score Capability. The Fable fallback composite is
  rejected. Average turns, output-token summaries, and calculated cost components remain
  diagnostic because Elo is not a binary success denominator and the source cost uses live typical
  cache-hit measurements rather than a deployment- and billing-record-bound task ledger.

## Publication assertions

- Five exact canonical named-release configurations are visible, each with label-exact identity and
  first-party nominal pricing record.
- The configured capability matrix contains 75 model/benchmark cells: 32 ready scored, 3 diagnostic
  measurements, 1 diagnostic reference, 1 vendor-claim-only, and 38 missing.
- Every model-specific score is labeled `real evidence — model-specific partial estimate`; it is not
  a UMI rank. Opus, Sol, and Kimi use eight of 15 Capability families across four domains with
  75.125% coverage; GLM uses seven families across four domains at 61.375%; Fable remains on one
  family at 8.25%. Opus, Sol, Kimi, and GLM clear the Capability-only coverage and breadth gates,
  but not the complete headline gates.
- Every publishable rank and every `headline_overall` remains null.
- The retained Opus/Kimi/GLM comparison certificate is provisional and source-bound; it is not a
  headline UMI score or public universal rank.
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

- exact-configuration, common-cohort capability results for the 38 missing cells, beginning with
  Fable HLE without fallback, Terminal-Bench, agentic work, and long-context/reliability evidence;
- arithmetic-mean attempt-level cost, input/output/cache-token use, wall time, turn count, and task
  success for the five models across at least three configured workload categories;
- independent replication or auditable raw result artifacts for vendor-only claims;
- fixed, versioned workload baskets for nominal-price scenario estimates, kept separate from
  observed successful-task Economics;
- empirical calibration or decorrelation of within-domain family budgets, a longitudinal reference
  cohort, and formal uncertainty propagation.

The next ingestion milestone targets the exact τ³-Banking public cohort, followed by one complete
five-model task-level workload cohort. The current gates must remain closed until those artifacts
exist; missing evidence must not be inferred, imputed, or reweighted away.
