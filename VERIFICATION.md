# UMI verification record

## UMI Public v0.5 Governed on feat/umi-v05-governed-public

Verified on 2026-08-17 from `feat/umi-v05-governed-public`. Named candidates Grok 4.5 High
and Gemini 3.1 Pro Preview are diagnostic abstentions. No invented scores. No paid requests.

| Check | Outcome |
|---|---|
| `uv run pytest --cov=umi --cov=analysis --cov-fail-under=90` | 212 passed; 92.48% coverage |
| `uv run ruff check .` | passed |
| `uv run mypy --strict umi analysis scripts` | passed; 69 source files |
| `umi edition --edition v0.5 validate` | valid |
| `umi edition --edition v0.5 audit` | valid; five-pilot reproduction exact |
| `umi edition --edition v0.5 candidates` | both `insufficient_common_support`; `umi_public` null; headline_additions empty |
| `umi edition --edition v0.5 blockers` | 12 documented blockers; every `umi_public` null |
| `umi edition --edition v0.5 certificate` | published_governed_index |
| v0.4 five-pilot reproduction | exact |
| v0.4 golden SHA-256 set | `tests/test_v04_legacy_freeze.py` passed |
| Paid OpenRouter / live execute | not run |

## UMI Public v0.4 on main

Verified on 2026-08-17 from `main` on Windows. UMI Public publishes five `umi_public`
scores from frozen Epoch extracts. v0.3 processed artifacts and `headline_overall`
nulls are unchanged. No API keys and no paid requests.

| Check | Outcome |
|---|---|
| `uv run pytest --cov=umi --cov=analysis --cov-report=term-missing --cov-fail-under=90` | 191 passed; 92.60% coverage |
| `uv run ruff check .` | passed |
| `uv run mypy --strict umi analysis scripts` | passed; 61 source files |
| `PYTHONPATH=. uv run --no-sync umi edition --edition v0.4 validate` | `{"edition":"umi-public-v0.4","valid":true}` |
| `PYTHONPATH=. uv run --no-sync umi edition --edition v0.4 score` | published; fingerprint `e266af13b966cf79cfc5086513ec35f60cf2194f896f41f4b332f60ac9788e6d` |
| `PYTHONPATH=. uv run --no-sync umi edition --edition v0.4 dashboard` | writes HTML with rank bars, stacked contributions, grouped components, Capability heatmap, plus ranking/series CSVs; does not rescore |
| `uv run python -m scripts.build_v04_public` | Sol 66.27, Kimi 59.69, Opus 55.51, Fable 54.43, GLM 54.20 |
| `PYTHONPATH=. uv run --no-sync umi edition --edition v0.3 validate` | infeasible as a Public edition, as designed |
| `PYTHONPATH=. uv run --no-sync umi estimates --data-dir data/pilots/v0.3/raw` | five model-specific partials; all `headline_overall` null |
| v0.3 golden SHA-256 set | `tests/test_v03_legacy_freeze.py` bytes unchanged |
| Paid OpenRouter / live execute | not run |

# UMI v0.3.16 verification record

Verified on 2026-08-17 from `main` on Windows with the Python 3.11+ project contract.
This release hardens the offline OpenRouter runner state machine. It does not execute the
paid 350-request cohort, does not admit an operational ledger, and does not change scored
fingerprints, coverage, or headline gates. Formula identity remains `umi-methodology-v0.3.15`.

The prior v0.3.15 hosted Linux/Windows CI evidence is retained below.

## v0.3.16 offline runner hardening

| Check | Outcome |
|---|---|
| `uv run pytest` | 171 passed |
| `uv run pytest --cov=umi --cov=analysis --cov-report=term-missing --cov-fail-under=90` | 171 passed; 93.33% core package and analysis coverage; live acquisition/execution behavior is still verified separately rather than through mocked HTTP |
| `PYTHONPATH=. uv run --no-sync ruff check .` | passed |
| `PYTHONPATH=. uv run --no-sync mypy --strict umi analysis scripts` | passed, 55 source files |
| offline `scripts.run_openrouter_operational_pilot --status` on a clean run contract | passed; 350 pending attempts, remaining ceiling `$39.455197`, `finalize_possible` false; no network and no writes |
| crash/resume unit tests over frozen local artifacts | passed; HTTP helpers unused; request-started, request-error, request-bytes drift, raw-body checksums, identity/cost `review-error.json`, remaining-cost invariance, ledger region rejection, and incomplete 350-result finalize all fail closed |
| `umi operational preflight --task-pack ... --run-manifest ...` | passed; still 70/5/350 and `$39.455197` |
| documented validation, ingestion, scoring, comparison, analysis, and certificate CLI flows | passed with valid JSON output |
| live `--preflight` / `--execute` | not run; no paid request |

## Prior v0.3.15 verification record

Verified on 2026-08-16 from `main` on macOS with Python 3.14.3 against the Python 3.11+
project contract.

## Commands and outcomes

| Check | Outcome |
|---|---|
| `uv sync --frozen --extra dev --no-editable --reinstall-package unified-model-index` | passed; installed the locked UMI environment; isolated UMI 0.3.15 wheel verification is recorded below |
| `uv run --no-sync python -m scripts.build_v03_pilot` | passed; rebuilt all raw and processed pilot artifacts offline |
| schema equality test against `umi.schema_export.rendered_schemas()` | passed; committed machine-readable schemas remain current |
| `uv run pytest` | 156 passed |
| `uv run pytest --cov=umi --cov=analysis --cov-report=term-missing --cov-fail-under=90` | 156 passed; 93.34% core package and analysis coverage; live acquisition/execution behavior is verified separately rather than through mocked HTTP |
| `PYTHONPATH=. uv run --no-sync ruff check .` | passed |
| `PYTHONPATH=. uv run --no-sync mypy --strict umi analysis scripts` | passed, 55 source files |
| `umi sources validate --strict` | passed; complete registry, crosswalk, licensing, attribution, diagnostic, pricing, and release-claim audit is valid |
| `umi crosswalk` and `umi overlap` | passed |
| `umi bundle validate --data-dir data/pilots/v0.3/raw` | passed; acceptance manifest admits 53 records and excludes 8 diagnostic records with 0 unready scored records |
| all seventeen offline `umi ingest --source ...` commands | passed: AA composite facts, AA HLE, AA GDPval, AA-LCR, AA Omniscience, AA τ³-Banking, AA Terminal-Bench v2.1, CursorBench, Epoch ECI, Epoch benchmarks, both Arena cohorts, DeepSWE, and four lab-release sources |
| `umi attempts aggregate --ledger ...` | passed; deterministic order-independent aggregation preserves per-metric denominators, splits partial diagnostics, rejects duplicate IDs and unverified ready deployments, emits no finite Economics at zero success, and requires complete provider-billing evidence for observed successful-task cost |
| `umi operational preflight --task-pack ... --run-manifest ...` | passed; exact 70-task/14-category pack, five deployments, 350 requests, fingerprints, provider/snapshot/effort/tier mappings, balanced cyclic execution order, and conservative `$39.455197` maximum router-price ceiling including worst-case cache-write tariffs verified offline |
| live `scripts.run_openrouter_operational_pilot --accept-network --preflight ...` | passed; all five exact snapshots, selected provider endpoints, supported efforts/parameters, service-tier request, context/output limits, and input/output/cache prices matched the frozen run manifest; the account was correctly reported unfunded at `-$0.04646605` remaining |
| live paid-path credit gate with `--execute --accept-cost --max-cost-usd 39.455197 ...` | exited 2 before any paid request because available credits did not cover the ceiling; only the fingerprinted, exact-runner-source-bound v0.2 run contract was created and the temporary run contained zero request, request-started, or response artifacts |
| official OpenRouter billing-semantics review | response `usage.cost` is documented as the total account charge and authenticated generation metadata independently exposes `total_cost`; derived billing promotion now additionally requires a complete run and exact before/after account-credit reconciliation within `$0.00000005` |
| deterministic MMLU-Pro task-pack regeneration | passed byte-for-byte from the pinned 12,032-row MIT parquet at SHA-256 `0e24a191921c2f453518a537a8b2117bd137e7714d4ef1565e9ba06c1ecb9ad8` |
| controlled-workload authority and scoring invariance | passed; the exact MMLU-Pro cohort maps only to the new one-turn knowledge/reasoning family under General Interaction's configured 10% category weight; all existing numerical pilot estimates, comparison scores, ranks, and null headlines remain unchanged, while `scored_data_fingerprint` changed from `fdfac327…7bf136` to `ffa7c3bf…f89fe9` |
| documented validation, ingestion, scoring, comparison, analysis, and certificate CLI flows | passed with valid JSON output |
| five-model and three-model common-evidence comparisons | passed; Kimi DeepSWE remains 25.0 on the identical five-model panel, and every raw/normalized contribution carries panel and scale identity |
| joint comparison sensitivity | passed; 32 exhaustive five-model scenarios and 512 exhaustive three-model scenarios, with possible-rank and robust-dominance envelopes and no probability claims; the retained Opus/Kimi/GLM ranks remain robust at 1/2/3 after adding Terminal-Bench |
| `umi certificate` for Opus/Kimi/GLM | passed; eleven common stable panels, 33 selected records, nine exact artifact checksums, 512 joint scenarios, deterministic result fingerprint `bf1c8f3a…e91b0e` and scored-input fingerprint `ffa7c3bf…f89fe9` |
| portable dashboard packaging | passed at 1440 px and 390 px; 17 delivered blocks, eleven charts, and four metrics rendered; source dialog passed; no overflow, external-request, or browser-error failure |
| consecutive complete pilot rebuilds plus schema regeneration | passed byte-for-byte with no artifact or schema drift |
| `uv build` plus fresh temporary-environment wheel install outside the checkout | passed locally on Python 3.14.3 with wheel SHA-256 `48a0518bca8b843996a27c141f846a32d42b6ada596369f8a212b1135886fd7a`; `import umi`, `umi --help`, and an isolated three-model comparison passed; hosted Python 3.11 and 3.14 wheel checks passed in run `31943817385` |
| `scripts/verify_deepswe_trial_ledger.py --accept-network` | passed against official ledger SHA-256 `13d6f7563330110231b008ae4eb38e03de24af08acead840de296d1127144971`; reconciled 27,558 total rows, 2,257 selected rows, 2,231 scored attempts, 26 excluded error rows, all five success/resource means, and Fable cost coverage of 432/436 attempts |
| `umi validate --data-dir tests/fixtures --config-dir tests/fixtures/config` | passed without a source registry; schema and selected scored inputs are valid |
| previously verified explicit Epoch/Arena network acquisition evidence | retained unchanged with its checksum manifest; this milestone additionally used the explicitly acknowledged read-only OpenRouter preflight and insufficient-credit execution gate recorded above; no completion request was made |

The normal `uv run` auto-sync path creates an editable installation. Python 3.14 ignores the
underscore-prefixed editable `.pth` emitted in this environment, so the verified workflow installs a
wheel with `--no-editable` and uses `--no-sync` for subsequent commands. This is documented in the
README rather than hidden as a local workaround.

The most recent completed GitHub Actions baseline is
[run 31943817385](https://github.com/lukifer23/UMI---Unified-Model-Index/actions/runs/31943817385)
for UMI v0.3.15 workload-authority commit `32a2109`. It completed successfully. Linux passed the full quality, schema,
governed validation, deterministic rebuild, CLI, and isolated-wheel gates. Linux 3.11 and 3.14 each
passed the test suite plus isolated-wheel import/help/comparison smokes. Windows 3.12 passed tests,
generic validation, governed bundle validation, strict source/checksum audit, deterministic rebuild
diff, and the three-model comparison smoke. These hosted results—not the local macOS run—establish
the recorded Linux and Windows compatibility claim. The Python 3.11/3.14 jobs preserve the governed
`math.fsum` cross-version regression gate. CI selects the wheel matching the package version instead
of the lexically first wheel, preventing stale local artifacts from testing an older release.
GitHub emitted only Node 20 deprecation annotations for `actions/checkout@v4` and
`astral-sh/setup-uv@v6`; no UMI job failed.

## Acquisition reconciliation

- MMLU-Pro's complete 12,032-row test parquet is frozen from revision
  `b189ec765aa7ed75c8acfea42df31fdae71f97be` at SHA-256
  `0e24a191921c2f453518a537a8b2117bd137e7714d4ef1565e9ba06c1ecb9ad8` under the MIT License.
  The derived pack selects five tasks from each of 14 literal categories by the documented seeded
  SHA-256 order. A fresh derivation from the frozen parquet is byte-identical to the committed pack.

- The newly acquired Epoch CSV is byte-identical to the frozen reviewed artifact at SHA-256
  `946538f24b2d16cbbccc54c554d86e5afb6d4b3f175bf9bdeae2af61869658b6`.
- The complete Epoch Benchmarking Hub archive is frozen at SHA-256
  `35a7c21ba7d535514ebcf9bbe7b8265d2e2da40ef6b1fa63fe49323c3395a18b`;
  four exact Max-effort rows each for GPQA Diamond, SciCode, and CritPt are adapted from the raw CSV
  members. Fable is rejected because fallback absence is not established for GPQA and is explicitly
  contradicted by fallback-composite labels for SciCode and CritPt.
- A read-only 2026-08-16 check of Epoch's current official
  `https://epoch.ai/data/benchmark_data.zip` returned archive SHA-256
  `83ec36db3683533c3cda6d6cef1098ae2677a9650cd4cee6e06ea6cf1917d2d9`. Its
  `arc_agi_2_external.csv` member has SHA-256
  `e3a717d3e7d2e57deb91fd084e9d1063e9f30fd13dcc7de3a23613a9692fca2b`: it contains one
  GLM-5.2 row explicitly labeled `glm-5.2_unknown` and no Fable row. The unknown-effort GLM result
  cannot crosswalk to the pilot's exact Max configuration, so both capability gaps remain missing;
  the live review is not admitted as a frozen scored artifact.
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
- Operational comparison identity now binds interaction mode, operational profile, versioned success
  definition, and cohort; incompatible task semantics cannot share normalization panels or Pareto
  series.
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
data/operational/pilot-v0.1/      frozen 70-task pack and exact five-deployment run contract
data/sources/v0.3/                frozen artifacts, reviewed facts, exact crosswalk
schemas/                          generated JSON Schemas
scripts/build_v03_pilot.py        deterministic offline assembly
scripts/freeze_v03_open_sources.py explicit, immutable network acquisition
scripts/run_openrouter_operational_pilot.py explicit cost-gated live executor
scripts/verify_deepswe_trial_ledger.py explicit checksum-pinned facts verification
tests/test_operational_runner.py  offline run-contract and artifact-integrity gates
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

Paid execution of the frozen MMLU-Pro cohort is out of scope for the first ranking product. That
cohort can fill at most the 10% general-interaction family. Completing every currently approved
workload (DeepSWE, Terminal-Bench, CursorBench, and MMLU-Pro) still tops out at 0.35 Efficiency
and 0.35 Economics coverage, below the 0.50 / 0.40 gates. Additional Capability sources are useful
only when they close a configured cell or materially strengthen source diversity; they do not
substitute for the operational evidence blocking Overall. The current gates must remain closed
until approved families exist outside coding plus general interaction **and** DeepSWE-class public
ledgers fill them; missing evidence must not be inferred, imputed, reweighted, or replaced by
published calculated cost-per-task.

The first official ranking product is the existing Opus / Kimi / GLM Capability certificate. It is
not `headline_overall`.
