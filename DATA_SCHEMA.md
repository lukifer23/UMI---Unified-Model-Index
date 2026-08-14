# UMI v0.3 data schema

The generated JSON Schemas in `schemas/` are the machine-readable authority. This document explains
their intended use. Run `python scripts/generate_schemas.py` after changing a Pydantic model; the test
suite fails if committed schemas drift.

All Pydantic records are frozen, reject unknown fields, and reject source NaN and infinity. IDs match
`^[a-z0-9][a-z0-9._-]*$`. YAML is an immutable input format; derived results retain source record IDs.

## Dataset files

`load_dataset(DATA_DIR)` reads these top-level lists:

| File | Key | Record type |
|---|---|---|
| `models.yaml` | `models` | `ModelConfiguration` |
| `benchmarks.yaml` | `measurements` | `BenchmarkMeasurement` |
| `pricing.yaml` | `pricing` | `PricingRecord` |
| `task_efficiency.yaml` | `measurements` | `EfficiencyMeasurement` |
| `task_economics.yaml` | `measurements` | `TaskEconomicsMeasurement` |
| `external_indexes.yaml` | `measurements` | `ExternalIndexMeasurement` |

## Common provenance

Every measurement contains:

```yaml
record_id: unique-record-id
source:
  organization: Evaluator name
  url: https://source.example/result
  accessed: 2026-08-14
result_type: independent  # independent | community_reproduction | vendor_reported | derived
record_status: ready      # ready | diagnostic_only | synthetic | invalid
signal_role: task         # composite | preference | task | efficiency | economics | reference
scoring_disposition: scored  # scored | diagnostic_only
metric_definition: Exact numerator, denominator, aggregation, and interpretation
benchmark_version: published-version
harness_version: published-harness-version
evaluator: Evaluator name
harness_owner: Harness owner
run_executor: Run executor
raw_artifact_available: true
capture_type: reviewed_fact_extract
source_artifact_id: registry-snapshot-id
source_registry_snapshot_id: registry-snapshot-id
crosswalk_entry_id: exact-crosswalk-entry-id
signal_id: overlap-policy-signal-id
reproducible: false
configuration_verified: true
serving_provider: Optional serving provider
endpoint_id: Optional immutable endpoint/deployment ID
service_tier: Optional service tier
```

Optional notes and tool metadata preserve published context. Readiness requirements are enforced by
record type and model status; missing published sample-size fields remain null rather than invented.
The three governance bindings and `capture_type` are mandatory for scored real-data records at
bundle validation, while remaining optional for diagnostic records and isolated synthetic fixtures.
Capture type distinguishes a raw upstream payload, archived source snapshot, reviewed fact extract,
citation-only reference, or derived artifact; it does not by itself imply reproducibility.

## Model configuration and deployment

```yaml
id: model-config-id
family: Marketing family
provider: Model developer (legacy-compatible field)
model_developer: Optional explicit developer
release_date: 2026-07-09
configuration: max
snapshot_id: immutable-snapshot-id
api_model_id: Optional provider model identifier
serving_provider: Optional deployment provider
endpoint_id: Optional immutable serving endpoint
service_tier: Optional tier
region: Optional region
hardware: Optional material hardware
source_snapshot_ids: [registry-snapshot-id]
open_weights: false
synthetic: false
```

`configuration` is one of `standard`, `off`, `low`, `medium`, `high`, `max`, `xhigh`, or `custom`.
Capability may omit deployment fields only when the source genuinely evaluates a model snapshot
independently of serving. Deployment-dependent records must match configured deployment fields.

## Benchmark configuration

Benchmark definitions specify `id`, `name`, `domain`, `family`, `direction`, `unit`, positive
`representation_weight`, normalization, optional `representation_group`, and aggregate/constituent
links. Aliases use the same representation group. Families specify `id`, domain, weight, and cap.

Family weights in each represented domain sum to one, every weight is at most its cap, and caps sum
to at least one. Aggregate/constituent links must stay inside one family.

Benchmark measurements add:

```yaml
benchmark_id: benchmark-id
model_id: model-config-id
model_snapshot_id: immutable-snapshot-id
value: 72.4
cohort_key: benchmark-harness-v3-pass1-tools
evaluation_date: 2026-08-10
evaluation_settings: {reasoning_effort: max, pass_at_k: 1}
number_of_tasks: 500       # optional
number_of_trials: 1        # optional
sample_count: 500          # optional
pass_at_k: 1               # optional
uncertainty:
  kind: published_margin  # confidence_interval | published_margin | standard_error
  margin: 1.6
  source_fields: [publisher_margin_column]
  confidence_level: null  # never inferred
```

The unit must be a supported enum and percentages/rates must respect their declared bounds.

## Efficiency and Economics

Efficiency measurements require model/workload/category/cohort identity, attempts, success rate in
`[0,1]`, and at least one nonnegative observation:

```yaml
model_id: model-config-id
model_snapshot_id: immutable-snapshot-id
workload: workload-id
workload_category: coding_agents
cohort_key: workload-harness-v2
evaluation_date: 2026-08-10
attempts: 100
success_rate: 0.72
mean_total_tokens: 12000
mean_turns: 8
mean_wall_seconds: 91
mean_tool_calls: 14
mean_cost_per_attempt: 1.35
```

Supported workload categories are `coding_agents`, `research_analysis`, `tool_use_agents`,
`browser_computer_use`, `general_interaction`, and `long_horizon`. Legacy short aliases migrate on
load. Success-adjusted derived values are not stored back into YAML.

Task Economics records use `cost_basis: attempted_task|successful_task`, nonnegative
`mean_cost_usd`, and `aggregation_statistic: arithmetic_mean|median|total|unspecified`. Only
arithmetic means can enter mean-based success adjustment. UMI never joins a numerator and rate from
different records or silently treats a median, total, or ambiguous “average” as a mean.

Pricing records preserve advertised input/output/cache/reasoning/tool prices but do not substitute
for observed successful-task Economics in v0.3. `cache_write_per_million` is the ordinary or
five-minute write tariff; `cache_write_1h_per_million` retains a separately published one-hour
write tariff. Missing cache-write or storage prices remain absent rather than being encoded as zero.

## External indexes

External index records preserve an index ID, model/snapshot, value, unit, direction, cohort, date,
and full provenance. In v0.3, AA indices, Epoch ECI rows, and Arena text/style-control ratings are
explicitly diagnostic-only and excluded from the scored-data fingerprint.

## Source, crosswalk, overlap, and adapter contracts

`ScoringBundle` is the enforced real-data boundary. It combines the dataset, configuration, source
registry, exact crosswalk, overlap policy, and verified artifact manifest. Normal real-data analysis
refuses to score if a scored record lacks an exact signal, crosswalk, registry, checksum, revision,
role, disposition, or budget binding.

Each source snapshot requires content type, upstream revision, adapter ID, license ID, attribution,
redistribution scope, artifact path, and SHA-256. Missing documentation, missing files, or checksum
mismatches fail validation.

Each crosswalk entry records the literal source model identifier and effort, canonical configuration
and effort, match evidence, artifact revision, and exact/rejected status. Exact entries require equal
non-null effort; rejected entries require a reason. Duplicate aliases and many-to-one collisions are
invalid.

The directed overlap graph uses `contains`, `derived_from`, `duplicate_measurement`, `shared_tasks`,
`shared_construct`, and `unknown_overlap` edges. Cycles and unrestricted scored
aggregate/constituent pairs are invalid.

Each offline adapter returns accepted typed records, diagnostic records, rejected rows, and stable
diagnostics. Rejected and diagnostic evidence affects the complete audit fingerprint; only accepted
scoring records affect the scored-data fingerprint.

## Validation result

`umi validate` separates structure from readiness:

```json
{
  "schema_valid": true,
  "scoring_ready": false,
  "errors": [],
  "readiness_failures": ["record x: immutable model snapshot is unspecified"],
  "warnings": []
}
```

Structural/referential errors include duplicate IDs, unknown models/benchmarks, snapshot collisions,
invalid family budgets, invalid status, and multiple ready cohorts without a merge policy.
Readiness failures exclude records from normal scoring without pretending the YAML is malformed.

## Scoring result

See `schemas/scoring-result.schema.json` for all fields. Important output distinctions are:

- `partial_overall_estimate`: reweighted analytical estimate over available components;
- `headline_overall`: null unless every headline eligibility invariant passes;
- component `score`, hierarchical `coverage`, `provisional`, provenance IDs, and diagnostics;
- `scoring_ready`, `eligible`, confidence and explicit confidence reasons;
- Value scenario, formula, and parameters;
- detailed domain/family/representation/metric/workload/source coverage;
- `dataset_fingerprint`, `scored_data_fingerprint`, `cohort_id`, `data_as_of`, version metadata, and
  release window.

JSON output is deterministic and disallows NaN/infinity. CSV output flattens nested fields and joins
lists with `|`.

## Configuration files

- `weights.yaml`: domain, Efficiency metric, workload, Overall, and sensitivity weights;
- `benchmarks.yaml`: families and benchmark representations;
- `eligibility.yaml`: release window, component/Overall coverage, breadth, and confidence thresholds;
- `normalization.yaml`: cohort thresholds, default strategy, correlation overlap, and log metrics;
- `value.yaml`: named, distinct experimental Value scenarios and baseline.
- `overlap.yaml`: signal roles, dispositions, budget groups, and directed overlap evidence.

Every scoring-relevant field must affect behavior. Configuration is canonically serialized and
hashed into `config_fingerprint`.
