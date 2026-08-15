# UMI v0.3.12 verification record

Verified on 2026-08-15 from `main` on macOS with Python 3.14.3 against the Python 3.11+
project contract.

## Commands and outcomes

| Check | Outcome |
|---|---|
| `uv sync --frozen --extra dev --no-editable --reinstall-package unified-model-index` | passed; installed UMI 0.3.12 as a wheel from the committed lock |
| `uv run --no-sync python -m scripts.build_v03_pilot` | passed; rebuilt all raw and processed pilot artifacts offline |
| schema equality test against `umi.schema_export.rendered_schemas()` | passed; committed machine-readable schemas remain current |
| `uv run pytest` | 133 passed |
| `uv run pytest --cov=umi --cov=analysis --cov=scripts --cov-report=term-missing --cov-fail-under=90` | 133 passed; 91.91% combined coverage |
| `PYTHONPATH=. uv run --no-sync ruff check .` | passed |
| `PYTHONPATH=. uv run --no-sync mypy --strict umi analysis scripts` | passed, 51 source files |
| `umi sources validate --strict` | passed; complete registry, crosswalk, licensing, attribution, diagnostic, pricing, and release-claim audit is valid |
| `umi crosswalk` and `umi overlap` | passed |
| `umi bundle validate --data-dir data/pilots/v0.3/raw` | passed; acceptance manifest admits 53 records and excludes 8 diagnostic records with 0 unready scored records |
| all seventeen offline `umi ingest --source ...` commands | passed: AA composite facts, AA HLE, AA GDPval, AA-LCR, AA Omniscience, AA τ³-Banking, AA Terminal-Bench v2.1, CursorBench, Epoch ECI, Epoch benchmarks, both Arena cohorts, DeepSWE, and four lab-release sources |
| documented validation, ingestion, scoring, comparison, analysis, and certificate CLI flows | passed with valid JSON output |
| five-model and three-model common-evidence comparisons | passed; Kimi DeepSWE remains 25.0 on the identical five-model panel, and every raw/normalized contribution carries panel and scale identity |
| joint comparison sensitivity | passed; 32 exhaustive five-model scenarios and 512 exhaustive three-model scenarios, with possible-rank and robust-dominance envelopes and no probability claims; the retained Opus/Kimi/GLM ranks remain robust at 1/2/3 after adding Terminal-Bench |
| `umi certificate` for Opus/Kimi/GLM | passed; eleven common stable panels, 33 selected records, nine exact artifact checksums, 512 joint scenarios, deterministic result fingerprint `5e719699…92eea12` and scored-input fingerprint `bffc0aa8…eea8c1` |
| portable dashboard packaging | passed at 1440 px and 390 px; 17 delivered blocks, eleven charts, and four metrics rendered; source dialog passed; no overflow, external-request, or browser-error failure |
| consecutive complete pilot rebuilds plus schema regeneration | passed byte-for-byte with no artifact or schema drift |
| `uv build` plus fresh temporary-environment wheel installs outside the checkout | passed on Python 3.11.15 and 3.14.3 with wheel SHA-256 `f01129c636687651eddf737d9c8fa19b0eee4ec3e38e17b189c66d8aa0f04ec8`; `import umi`, `umi --help`, and certificate output passed, and both interpreters emitted byte-identical certificates matching the governed artifact |
| `scripts/verify_deepswe_trial_ledger.py --accept-network` | passed against official ledger SHA-256 `13d6f7563330110231b008ae4eb38e03de24af08acead840de296d1127144971`; reconciled 27,558 total rows, 2,257 selected rows, 2,231 scored attempts, 26 excluded error rows, all five success/resource means, and Fable cost coverage of 432/436 attempts |
| `umi validate --data-dir tests/fixtures --config-dir tests/fixtures/config` | passed without a source registry; schema and selected scored inputs are valid |
| previously verified explicit Epoch/Arena network acquisition evidence | retained unchanged with its checksum manifest; the only network operation for this milestone was the explicit, checksum-pinned DeepSWE verification above |

The normal `uv run` auto-sync path creates an editable installation. Python 3.14 ignores the
underscore-prefixed editable `.pth` emitted in this environment, so the verified workflow installs a
wheel with `--no-editable` and uses `--no-sync` for subsequent commands. This is documented in the
README rather than hidden as a local workaround.

GitHub Actions [run 31891087375](https://github.com/lukifer23/UMI---Unified-Model-Index/actions/runs/31891087375)
for UMI v0.3.12 commit `b358d30` completed successfully. Linux passed the full quality, schema,
governed validation, deterministic rebuild, CLI, and isolated-wheel gates. Linux 3.11 and 3.14 each
passed the test suite plus isolated-wheel import/help/comparison smokes. Windows 3.12 passed tests,
generic validation, governed bundle validation, strict source/checksum audit, deterministic rebuild
diff, and the three-model comparison smoke. These hosted results—not the local macOS run—establish
the recorded Linux and Windows compatibility claim. The Python 3.11/3.14 jobs preserve the governed
`math.fsum` cross-version regression gate. CI selects the wheel matching the package version instead
of the lexically first wheel, preventing stale local artifacts from testing an older release.
GitHub emitted only Node 20
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
- τ³-Banking is retained as a facts-only artifact at SHA-256
  `838c0c02ec932059b10a4172123e6ecd6b916c10eba2da105c7751b27614bad9`. Four exact Max-effort
  pass@1 rows score Capability across the 97-task, five-repeat cohort. The Fable fallback composite
  is rejected. Incomplete operational fields, calculated rather than billed costs, and conflicting
  public decode-time units remain diagnostic.
- AA-LCR is retained as a facts-only artifact at SHA-256
  `7d736d8a6dbbfcf1ea8815ab95847284fc7fdb0ec3e90887ab5cbf198e53d221`. Four exact Max-effort
  pass@1 rows score Capability across the 100-question, three-repeat v4.1.1 cohort. The Fable
  fallback deployment is rejected. Provider-specific token summaries, incomplete operational
  fields, and calculated rather than billed costs remain diagnostic.
- AA Omniscience is retained as a facts-only artifact at SHA-256
  `f5fbaa93bc0db372b28ffedc402f1a432c5d7ea0a320d0b75e511e3494e9679d`. Four exact Max-effort
  source-defined Index rows score Capability across the 6,000-question cohort. Accuracy, attempt,
  hallucination, answer counts, tokens, calculated cost, and time remain diagnostic. The Fable
  fallback deployment is rejected.
- AA Terminal-Bench v2.1 is retained as a facts-only artifact at SHA-256
  `cd785e4364a3119a7c1c0dd05346395cb61b2b57155228b5ab9032a957cabf97`. Four exact Max-effort
  pass@1 rows score Capability across the 89-task, three-repeat, 267-attempt Terminus 2 and E2B
  cohort. The Fable fallback deployment is rejected. Source-provided aggregate input, answer,
  reasoning, and cacheable-input token counts remain diagnostic because they are not a task-level
  attempt ledger, provider token accounting differs, and cacheable input is neither observed cache
  hits nor billed cache usage.
- DeepSWE's official 27,558-row trial ledger is checksum-pinned at SHA-256
  `13d6f7563330110231b008ae4eb38e03de24af08acead840de296d1127144971`. The explicit verifier
  reconciles all 2,231 scored attempts for the five Max configurations, their provider labels,
  pass counts, input/output/cache tokens, wall duration, agent steps, and means. Fable has cost on
  only 432 of 436 scored attempts; UMI now preserves that per-metric denominator, and the endpoint
  resource record remains diagnostic rather than borrowing the full-cohort success denominator.

## Publication assertions

- Five exact canonical named-release configurations are visible, each with label-exact identity and
  first-party nominal pricing record.
- The configured capability matrix contains 75 model/benchmark cells: 48 ready scored, 3 diagnostic
  measurements, 1 diagnostic reference, and 23 missing.
- Every model-specific score is labeled `real evidence — model-specific partial estimate`; it is not
  a UMI rank. Opus, Sol, and Kimi use 12 of 15 Capability families across five domains with 100%
  coverage; GLM uses 11 families across five domains at 86.25%; Fable remains on one family at
  8.25%. Opus, Sol, Kimi, and GLM clear the Capability-only coverage and breadth gates,
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
scripts/verify_deepswe_trial_ledger.py explicit checksum-pinned facts verification
tests/test_v03_pilot.py           adversarial source/scoring/publication tests
umi/adapters/                     pure offline source adapters
umi/                              validation, readiness, scoring, fingerprinting, CLI
```

## Remaining evidence required for a real headline UMI

- exact-configuration, common-cohort capability results for the 23 missing cells, beginning with
  Fable HLE, τ³-Banking, AA-LCR, and Terminal-Bench without fallback, plus additional
  context/reliability evidence;
- arithmetic-mean attempt-level cost, input/output/cache-token use, wall time, turn count, and task
  success for the five models across at least three configured workload categories;
- independent replication or auditable raw result artifacts for vendor-only claims;
- fixed, versioned workload baskets for nominal-price scenario estimates, kept separate from
  observed successful-task Economics;
- empirical calibration or decorrelation of within-domain family budgets, a longitudinal reference
  cohort, and formal uncertainty propagation.

The highest-value missing artifact remains one complete five-model task-level workload cohort with
deployment-bound success, cost, tokens, cache use, wall time, and turns. Additional capability
sources are useful only when they close a configured cell or materially strengthen source diversity;
they do not substitute for the operational evidence blocking Efficiency and Economics. The current
gates must remain closed until those artifacts exist; missing evidence must not be inferred, imputed,
or reweighted away.
