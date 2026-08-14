# UMI data schema

## v0.2 adversarial-hardening additions

- Models carry immutable `snapshot_id`, optional provider `api_model_id`, and
  `source_snapshot_ids` linking identity facts to the source registry.
- Provenance preserves evaluator, harness-owner, executor, raw-artifact,
  reproducibility, and configuration-verification metadata when known.
- Measurements carry `cohort_key`, `model_snapshot_id`, and `evaluation_date`;
  different cohort keys are never normalized together.
- Optional uncertainty fields preserve task/trial/sample counts, pass@k, standard
  error, and confidence intervals without pretending v0.2 propagates them.
- Benchmark configuration separates family `weight` and `cap` from each member's
  `representation_weight`.
- Workload categories are `coding_agents`, `research_analysis`,
  `tool_use_agents`, `browser_computer_use`, `general_interaction`, and
  `long_horizon`.
- Output has `partial_overall_estimate` and nullable `headline_overall`, never an
  ambiguous `overall`, plus Value methodology, confidence reasons,
  multi-dimensional coverage, and cohort identity.

## Real-pilot record types

`task_economics.yaml` stores observed task cost with an explicit `cost_basis` of
`attempted_task` or `successful_task`. Only successful-task records may enter
headline Economics. `external_indexes.yaml` stores third-party composite indexes
with their own unit, direction, cohort, and provenance; these records are reference
observations and do not enter UMI scoring.

`data/sources/registry.yaml` contains source snapshots with publication/as-of/access
dates, a relative artifact path, and SHA-256 checksum. Validation detects missing or
modified captures and warns when measurement URLs are absent from the registry.
`configuration_verified: true` means UMI verified the recorded configuration facts
against the cited source; it does not mean the evaluator run was independently
reproduced. `reproducible` records that separate property.

All raw files are YAML documents containing a top-level list named for the record type. IDs use lowercase ASCII letters, digits, dots, underscores, or hyphens and must begin with an alphanumeric character. Unknown fields are rejected.

## Provenance

```yaml
record_id: bm-synthetic-a
source:
  organization: UMI synthetic fixture
  url: https://example.invalid/umi/synthetic
  accessed: 2026-08-14
result_type: independent
benchmark_version: synthetic-v1
harness_version: synthetic-harness-v1
metric_definition: Synthetic percentage for tests only
tools_enabled: false
notes: SYNTHETIC TEST DATA
```

Valid result types are `independent`, `community_reproduction`, `vendor_reported`, and `derived`.

## Models

`models.yaml` contains `models`. Required fields are `id`, `family`, `provider`, `release_date`, `configuration`, and `open_weights`. Configuration effort is one of `standard`, `off`, `low`, `medium`, `high`, `max`, or `custom`. Optional fields include `context_window`, `notes`, and `synthetic`.

## Benchmark definitions and measurements

Definitions in `config/benchmarks.yaml` specify `id`, `name`, `domain`, `family`, direction, unit, weight, normalization strategy, optional parent aggregates, optional constituent IDs, and domain cap.

`benchmarks.yaml` contains measurements with `record_id`, `benchmark_id`, `model_id`, numeric `value`, provenance fields, and optional workload/evaluation settings. A record must resolve to known model and benchmark IDs.

## Pricing

`pricing.yaml` contains dated advertised prices per million tokens and tool charges. Prices are nonnegative USD values. Long-context surcharges are labeled strings mapped to nonnegative prices. Pricing is not interchangeable with observed task cost.

## Task efficiency and observed economics

`task_efficiency.yaml` contains records keyed by model and workload. Each record has a typed `workload_category`: `general`, `coding`, `agentic`, `research`, `browser`, or `multimodal`. Required observations are `attempts` and `success_rate` in `[0,1]`; optional nonnegative fields include token counts, turns, seconds, tool calls, and `mean_cost_per_attempt`. Derived effective metrics use the methodology's success adjustment. Zero success remains measured failure.

## Derived output

Score results contain `model_id`, component scores, Value, Overall, coverage percentage, confidence, eligibility, provisional status, domains represented, evidence-quality share, source record IDs, diagnostics, formula version, and configuration SHA-256 fingerprint. JSON output uses stable key ordering; CSV flattens lists with `|`.
