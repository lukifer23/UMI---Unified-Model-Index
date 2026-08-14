# UMI data schema

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

`models.yaml` contains `models`. Required fields are `id`, `family`, `provider`, `release_date`, `configuration`, and `open_weights`. Optional fields include `context_window`, `notes`, and `synthetic`.

## Benchmark definitions and measurements

Definitions in `config/benchmarks.yaml` specify `id`, `name`, `domain`, `family`, direction, unit, weight, normalization strategy, optional parent aggregates, optional constituent IDs, and domain cap.

`benchmarks.yaml` contains measurements with `record_id`, `benchmark_id`, `model_id`, numeric `value`, provenance fields, and optional workload/evaluation settings. A record must resolve to known model and benchmark IDs.

## Pricing

`pricing.yaml` contains dated advertised prices per million tokens and tool charges. Prices are nonnegative USD values. Long-context surcharges are labeled strings mapped to nonnegative prices. Pricing is not interchangeable with observed task cost.

## Task efficiency and observed economics

`task_efficiency.yaml` contains records keyed by model and workload. Required observations are `attempts` and `success_rate` in `[0,1]`; optional nonnegative fields include token counts, turns, seconds, tool calls, and `mean_cost_per_attempt`. Derived effective metrics use the methodology's success adjustment. Zero success remains measured failure.

## Derived output

Score results contain `model_id`, component scores, Value, Overall, coverage percentage, confidence, eligibility, provisional status, domains represented, evidence-quality share, source record IDs, diagnostics, and configuration SHA-256 fingerprint. JSON output uses stable key ordering; CSV flattens lists with `|`.

