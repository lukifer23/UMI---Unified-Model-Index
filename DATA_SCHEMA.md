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
capture_type: reviewed_fact_extract
source_artifact_id: registry-snapshot-id
source_registry_snapshot_id: registry-snapshot-id
crosswalk_entry_id: exact-crosswalk-entry-id
signal_id: overlap-policy-signal-id
reproducible: false
configuration_verification:
  model_label_exact: true
  release_label_exact: true
  effort_label_exact: true
  fallback_absent: true
  provider_snapshot_verified: false
  endpoint_verified: false
  service_tier_verified: false
  deployment_identity_verified: false
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
identity_kind: named_release
identity_assurance: label_exact
named_release: Published model release name
provider_snapshot_id: null  # only a genuine provider-published immutable identifier
open_weight_revision: null
api_model_id: Optional provider model identifier
serving_provider: Optional deployment provider
endpoint_id: Optional immutable serving endpoint
service_tier: Optional tier
region: Optional region
hardware: Optional material hardware
evidence_artifact_ids: [registry-snapshot-id]
open_weights: false
synthetic: false
```

`configuration` is one of `standard`, `off`, `low`, `medium`, `high`, `max`, `xhigh`, or `custom`.
Identity kind distinguishes immutable provider snapshots, immutable open-weight revisions,
versioned or dated endpoints, named releases, marketing configurations, and unknown identity.
Identity assurance is `verified`, `strongly_supported`, `label_exact`, `inferred`, or `unknown`.
Capability may use exact named-release evidence provisionally. Efficiency wall time, cached-token,
and cost fields and all Economics records require verified deployment identity. Exact harness-level
input/output/reasoning-token, turn, agent-step, and tool-call observations may score provisionally
without endpoint identity when the remaining identity and provenance gates pass.

## Benchmark configuration

Benchmark definitions specify `id`, `name`, `domain`, `family`, `direction`, `unit`, positive
`representation_weight`, normalization, optional `representation_group`, explicit
`selection_priority`, and aggregate/constituent
links. Aliases use the same representation group. Families specify `id`, domain, weight, and cap.

Family weights in each represented domain sum to one, every weight is at most its cap, and caps sum
to at least one. Aggregate/constituent links must stay inside one family.

Benchmark measurements add:

```yaml
benchmark_id: benchmark-id
model_id: model-config-id
source_model_id: exact-upstream-model-label
provider_snapshot_id: null
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

`workloads.yaml` defines the fixed category -> family -> workload hierarchy used for coverage and
aggregation. Family weights sum to one within each configured category, and workload weights sum to
one within each family. An observed workload must match its configured category and family; an
unconfigured workload cannot score.

Efficiency measurements require model/workload/category/cohort identity, attempts, success rate in
`[0,1]`, and at least one nonnegative observation:

```yaml
model_id: model-config-id
source_model_id: exact-upstream-model-label
provider_snapshot_id: null
workload: workload-id
workload_category: coding_agents
interaction_profile: autonomous_task
operational_profile_id: workload-harness-v2-autonomous
cohort_key: workload-harness-v2
evaluation_date: 2026-08-10
success_definition_id: fixed-evaluator-pass-v1
success_definition: Task passes the fixed workload evaluator.
attempts: 100
successful_attempts: 72
success_rate: 0.72
mean_input_tokens: 10000
mean_output_tokens: 2000
mean_turns: 8
mean_agent_steps: 9
mean_wall_seconds: 91
mean_tool_calls: 14
mean_cost_per_attempt: 1.35
observation_counts:
  input_tokens: 100
  output_tokens: 100
  turns: 100
  agent_steps: 100
  wall_seconds: 100
  tool_calls: 100
  cost_per_attempt: 100
```

Supported workload categories are `coding_agents`, `research_analysis`, `tool_use_agents`,
`browser_computer_use`, `general_interaction`, and `long_horizon`. Legacy short aliases migrate on
load. Success-adjusted derived values are not stored back into YAML. `mean_total_tokens` remains a
literal backward-compatible diagnostic field but is never added to separately weighted input and
output tokens. Every real, ready arithmetic-mean record requires an exact successful-attempt count
and a matching observation count for every populated mean. Counts may be lower on diagnostic
records so incomplete source summaries remain visible, but such a metric cannot score against the
full-cohort success denominator.

Task Economics records use `cost_basis: attempted_task|successful_task`, nonnegative
`mean_cost_usd`, and `aggregation_statistic: arithmetic_mean|median|total|unspecified`. Only
arithmetic means can enter mean-based success adjustment. UMI never joins a numerator and rate from
different records or silently treats a median, total, or ambiguous “average” as a mean.

### Attempt-level operational ledger

`schemas/attempt-ledger.schema.json` defines the frozen intake artifact used to produce operational
records. One ledger contains exactly one deployment, workload cohort, harness, operational-profile
ID, versioned success-definition ID and literal definition, and interaction profile
(`interactive_round` or `autonomous_task`). Ready ledgers require exact model, release, effort,
fallback absence, endpoint, service tier, and deployment verification plus a raw or archived
artifact and its SHA-256.

Each attempt has unique `attempt_id`, a stable `task_id`, explicit `success`, and independently
nullable nonnegative physical observations:

```yaml
attempts:
  - task_id: task-001
    attempt_id: task-001-run-01
    success: true
    input_tokens: 12000
    output_tokens: 2400
    reasoning_tokens: 800
    cache_read_tokens: 5000
    cache_write_tokens: 900
    turns: 6
    agent_steps: 14
    wall_seconds: 93.2
    tool_calls: 11
    retry_count: 1
    observed_cost_usd: 1.42
    billing_evidence: provider_billing_record
    cost_evidence_id: immutable-billing-row-reference
    provider_request_id: provider-request-reference
    generation_id: generation-reference
    resolved_model_id: provider/model-snapshot
    serving_provider: exact-provider
    service_tier: standard
    data_region: us
    upstream_id: provider-upstream-reference
```

Missing observations remain null; zero means observed zero. `observed_cost_usd` requires an explicit
billing-evidence kind and evidence reference. The offline aggregator sorts attempts by stable
identity, fingerprints the order-independent ledger, calculates each mean from its own denominator,
and splits complete and partial metrics. Cache-read populates the current cached-token Efficiency
metric; cache-write and retries remain explicit physical diagnostics. A successful-task Economics
record additionally carries attempt, success, and cost counts, total observed cost, and billing
evidence. It is ready only when provider-billing cost covers every attempt and at least one succeeds.
`schemas/attempt-ledger-aggregation.schema.json` defines this deterministic output.
Aggregation does not itself authorize scoring: the frozen artifact, registry entry, exact crosswalk,
and resulting scored bundle must still clear their ordinary validation gates.
Ready ledgers additionally require every attempt's resolved model, serving provider, service tier,
and any pinned region to agree with the single deployment identity. These per-attempt fields remain
in raw and derived output so a fallback or mixed deployment cannot hide behind a ledger-level label.
Router response cost remains diagnostic in the immutable attempt result. A derived ledger may label
it `provider_billing_record` only after the official response cost agrees with the authenticated
generation record for every attempt and the complete run sum reconciles to fingerprinted before/after
account-credit snapshots under the fixed methodology tolerance.

### Controlled task pack and run manifest

`schemas/controlled-task-pack.schema.json` defines a frozen task cohort bound to an upstream dataset
revision and file checksum. It preserves source row/question IDs, literal categories, source subsets,
questions, options, correct answers for offline grading, category counts, the deterministic selection
rule, and a canonical fingerprint. Task IDs and answer bindings must be unique and internally valid;
selected counts must match the tasks and remain balanced.

`schemas/operational-run-manifest.schema.json` binds that pack fingerprint to one or more exact UMI
deployments. Each deployment declares the canonical UMI configuration and the router model alias,
immutable endpoint snapshot, provider slug/name, endpoint name, requested and expected service tier,
endpoint reasoning effort, context/completion limits, reviewed input/output/cache-read/cache-write
per-token prices, run token ceiling, and intended exact crosswalk identity. The manifest also freezes
workload/cohort/harness/prompt/success identities, the no-tool delivery policy, and the deterministic
cyclic execution schedule. These contracts are acquisition/execution inputs, not scored measurements
or attempt ledgers; their crosswalk identities do not become governed crosswalk entries until a
completed artifact is admitted through the ordinary registry and bundle gates.

Pricing records preserve advertised input/output/cache/reasoning/tool prices but do not substitute
for observed successful-task Economics in v0.3. `cache_write_per_million` is the ordinary or
five-minute write tariff; `cache_write_1h_per_million` retains a separately published one-hour
write tariff. Missing cache-write or storage prices remain absent rather than being encoded as zero.

## External indexes

External index records preserve an index ID, canonical and upstream model identity, value, unit,
direction, cohort, date,
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
  "scored_inputs_ready": false,
  "strict_audit_valid": null,
  "headline_eligible": null,
  "errors": [],
  "readiness_failures": ["record x: model identity assurance is below label_exact"],
  "warnings": []
}
```

Structural/referential errors include duplicate IDs, unknown models/benchmarks, provider-snapshot collisions,
invalid family budgets, invalid status, and multiple ready cohorts without a merge policy.
Readiness failures exclude selected scored records from normal scoring without pretending the YAML
is malformed. Diagnostic-only records do not make `scored_inputs_ready` false. Ordinary validation
does not load the source registry by default and exits according to `schema_valid`.

`umi bundle validate` emits a typed acceptance manifest and validates the evidence used by scoring.
`umi sources validate --strict` validates the complete audit package. A diagnostic artifact can
therefore fail `strict_audit_valid` without invalidating a governed score that does not consume it.
`headline_eligible` remains a per-model scoring-result property, not a dataset-validation shortcut.

See `schemas/acceptance-manifest.schema.json` for the machine-readable manifest contract.

Capability components expose `evidence_profile_id`, `normalization_panel_ids`, `score_scale_id`,
and `score_semantics`. Each stable normalization panel binds one canonical benchmark representation,
cohort, complete accepted model panel, cohort roles, requested and applied strategies, transform,
configuration fingerprint, scored-input fingerprint, and full fallback trace. A score scale binds
the evidence profile and all contributing panels to the formula, normalization, and configuration
versions. Equality of evidence profile alone is not enough for direct normalized-score comparison.

Common comparisons carry raw benchmark values and source uncertainty as the primary results. Their
contributions also include raw unit and direction, absolute configured weight, requested versus
applied normalization, panel ID, normalized value, weighted contribution, and source record IDs.
The typed comparison result has either `status: ok` with scores, stable panels, a score scale,
deterministic sensitivity intervals, and per-model rank robustness, or
`status: insufficient_common_support` with empty scores, missing support by model, incompatible
series, recommended evidence, and an abstention publication label. Standard-error sensitivity is
explicitly labeled `derived_from_standard_error`, `normal_approximation`, and `z_value: 1.96`.
Scenario counts are endpoint combinations, not probabilities.

See `schemas/capability-comparison.schema.json` for the complete comparison contract.

## Public identity crosswalk

`config/editions/v0.4/crosswalk.yaml` and `config/editions/v0.5/crosswalk.yaml` bind each
scored entity to one Epoch `Model version`. Entries are `status: exact` only. Source
config IDs and entity IDs must carry the same effort token. Missing, duplicate, or
effort-mismatched bindings fail closed.

## Public edition policy

`config/editions/v0.4/` and `config/editions/v0.5/` are the live Public scoring policy.
`common-core.yaml` binds each series to an extract member, field, kind, optional harness
and panel filter, optional source-interval field, ablation flag, and evidence semantics.
Operational Efficiency series are `source_reported_resource_mean` with
`success_adjusted: false`. Access series are `source_reported_task_cost` with
`cost_evidence: source_reported`. Provider billing labels fail closed. `families.yaml`
supplies component, parent domain, and family weight. `normalization.yaml` supplies
logit ε, winsor, and high-effort suffixes. Unused families and unpaired interval
fields fail closed.

## Public anchor panels and score scales

`schemas/public-anchor-panels.schema.json` and `schemas/public-score-scales.schema.json`
are the contracts for named Public panels and frozen robust-z scales. A panel is a unique
set of Epoch config IDs. A scale binds one series to one panel plus transform, winsor,
median, and σ. `scale_id` is SHA-256 over those contents and the panel fingerprint.

## Public scoring bundle

`schemas/public-scoring-bundle.schema.json` is the machine-readable contract for governed
Public evidence. It binds identities, the Epoch zip SHA-256, and every common-core series
to typed `PublicEvidenceRecord` rows. `evidence_fingerprint` is SHA-256 over the edition,
zip checksum, and accepted config/entity/raw triples. The bundle does not score.

## Public index certificate

`schemas/public-index-certificate.schema.json` is the machine-readable contract for the UMI
Public v0.5 governed index. It binds the published scores to the Epoch zip SHA-256, license,
attribution, common-core series, validation result, partial intervals, rank ranges, and
pairwise interval overlap. `result_fingerprint` is SHA-256 over the certificate JSON excluding
that field. The certificate does not rescore. Overlapping partial intervals are
`indistinguishable_from`, not a claim of equal capability.

## Public uncertainty, source ablation, and rank stability

`schemas/public-uncertainty.schema.json` is the contract for the 2,048-draw partial
source-interval Monte Carlo. Each model row carries overall and component intervals, the
Monte Carlo rank range, and which series had published intervals. Pairwise rows carry
`p_left_greater` and a difference interval from the same draws. Family and
source-organization ablations are included on the same payload.

`schemas/public-source-ablation.schema.json` is the diagnostic Capability ablation contract.
It lists family drops, organization drops, emptied domains, `cannot_ablate` single-origin
components, and per-model diagnostic score ranges. It does not change `umi_public`.

`schemas/public-rank-stability.schema.json` binds published ranks to interval, ablation, and
weight-hypothesis rank ranges. `interval_stable` is a Monte Carlo fact. Overlapping partial
intervals stay `indistinguishable_from`.

## Public candidate audit

`schemas/public-candidate-audit.schema.json` is the machine-readable contract for v0.5 named
candidate certificates. An incomplete candidate serializes `status:
insufficient_common_support`, `headline_eligible: false`, and `umi_public: null`. The audit
lists present and missing common-core series and does not invent a score. Changing the
Access suffix panel to admit an unsuffixed WeirdML cost is out of scope for this schema.

## Public blocker report

`schemas/public-blocker-report.schema.json` is the machine-readable contract for unavailable
public evidence. Each row records missing series, affected model, required identity,
sources investigated, URLs investigated, the fail reason, and the evidence that would
resolve the blocker. `umi_public` is always null. The report does not rescore.

## Public weight sensitivity

`data/editions/v0.5/processed/weight-sensitivity.json` is a diagnostic recombination of
published component scores under named overall-weight hypotheses. It does not change
`umi_public` or the certificate ranks.

## Comparison certificate

`schemas/comparison-certificate.schema.json` is the authoritative contract. A certificate is a
deterministic projection of a validated scoring bundle and `CapabilityComparisonResult`; it does
not recalculate scores independently. `result_fingerprint` is SHA-256 over canonical certificate
JSON excluding that field. A supported result carries `evidence_profile_id`, panel and scale IDs,
raw and normalized contributions, rank robustness, identity assurance, selected record/artifact
IDs, and artifact checksums. An abstention has null profile/scale IDs and empty score/rank maps.

Components with no supported evidence serialize `score: null`, zero coverage,
`comparability_status: insufficient_common_support`, and `evidence_profile: null`; UMI does not emit
meaningless hashes of empty support. Correlation results suppress coefficients whenever
`interpretable` is false and provide `interpretability_reason`. Pareto output either binds every row
to one shared Capability profile and scale or returns `insufficient_common_support` with no rows.

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
