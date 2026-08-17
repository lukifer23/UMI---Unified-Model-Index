# UMI v0.4 Public Score — Full Coding-Agent Execution Specification

## Mission

Perform the architectural, methodological, data-ingestion, scoring, validation, uncertainty, documentation, and publication work required to produce a defensible **UMI Public score for all five pilot model configurations using only publicly available evidence**.

Do not stop after auditing, planning, or writing recommendations. Execute the work in the repository.

The five pilot configurations are currently:

1. Claude Opus 5 Max
2. Claude Fable 5 Max
3. GPT-5.6 Sol Max
4. Kimi K3 Max
5. GLM-5.2 Max

Treat the current repository state as authoritative. Names above are descriptive; verify and preserve the exact canonical model IDs used by the repository.

Repository:

```text
https://github.com/lukifer23/UMI---Unified-Model-Index
```

The new product must be informative, reproducible, source-bound, statistically honest, and genuinely useful. Do not create a superficial score merely to make five numbers appear.

---

# 1. Operating Rules

## 1.1 Execute rather than merely advise

* [ ] Inspect the current repository and current `HEAD`.
* [ ] Create an implementation branch, preferably:

```bash
git switch -c feat/umi-v0.4-public
```

* [ ] If that branch already exists, create a uniquely named branch rather than overwriting it.
* [ ] Preserve any existing uncommitted user changes.
* [ ] Do not use `git reset --hard`, `git clean -fd`, force pushes, or other destructive Git operations.
* [ ] Implement the complete plan as far as the publicly available evidence allows.
* [ ] Make reasonable engineering decisions without repeatedly requesting confirmation.
* [ ] Commit coherent phases separately with descriptive commit messages.
* [ ] If remote GitHub access is available and permitted, push the branch and open a draft pull request after all work is complete.
* [ ] If remote write access is unavailable, leave the repository on a clean local branch with organized commits.

## 1.2 Hard constraints

* [ ] Do not run paid OpenRouter evaluations.
* [ ] Do not use paid API requests to generate benchmark answers.
* [ ] Do not require the user to supply API keys.
* [ ] Do not use personal ChatGPT, Claude, Grok, OpenRouter, or other subscription credentials.
* [ ] Do not introduce Docker as a required dependency.
* [ ] Public HTTP downloads are permitted only through explicit acquisition commands.
* [ ] Every networked acquisition path must require an explicit flag such as `--accept-network`.
* [ ] Scoring, validation, certificate generation, and artifact rebuilds must remain fully offline.
* [ ] Do not silently scrape authenticated pages or bypass access controls.
* [ ] Do not redistribute raw source data when licensing or redistribution rights are unclear.
* [ ] Do not manually hardcode final UMI scores into generated outputs.
* [ ] Do not lower gates simply to force a headline score.
* [ ] Do not weaken source identity or provenance validation.
* [ ] Do not leave production `TODO`, placeholder, stub, mock, or `NotImplementedError` paths.
* [ ] Do not implement a second scoring engine inside the dashboard or report renderer.
* [ ] Do not regress the existing v0.3 outputs, commands, tests, certificates, or synthetic fixtures.

## 1.3 Quality standard

The implementation must be:

* Deterministic.
* Typed.
* Tested.
* Source-bound.
* Versioned.
* Rebuildable.
* Fail-closed.
* Transparent about modeled versus observed values.
* Explicit about uncertainty.
* Explicit about model/deployment identity.
* Comparable across the five pilot configurations.
* Reproducible without API keys.

---

# 2. Current Architectural Diagnosis

The existing repository has a strong governance and provenance foundation. Preserve it.

Strong existing elements include:

* Frozen source artifacts.
* Checksums.
* Exact crosswalks.
* Source registry.
* Acceptance manifests.
* Deterministic fingerprints.
* Typed schemas.
* Readiness filters.
* Diagnostic versus scored evidence.
* Structured abstention.
* Offline builds.
* Certificate generation.
* Golden artifact tests.
* CLI and package verification.

The problem is primarily the current scoring contract and evidence model.

## 2.1 The current Overall score is impossible by construction

The current Overall formula is approximately:

```text
0.55 × Capability
+ 0.25 × Efficiency
+ 0.20 × Economics
```

The current workload category basket includes weights similar to:

```text
coding_agents:          0.25
research_analysis:      0.20
tool_use_agents:        0.20
browser_computer_use:   0.15
general_interaction:    0.10
long_horizon:           0.10
```

However, the configured workload families currently cover only coding and general interaction.

Therefore, maximum theoretically attainable workload coverage is approximately:

```text
0.25 + 0.10 = 0.35
```

The existing publication gates require approximately:

```text
Efficiency coverage >= 0.50
Economics coverage  >= 0.40
Efficiency workload coverage >= 0.50
```

This means the current configuration cannot ever publish a headline Overall score, even with perfect data for every currently configured workload.

This must be fixed through edition-level policy redesign and static feasibility validation, not by lowering the gates.

## 2.2 Partial component scores are not automatically comparable

The current system can compute partial component values after reweighting available evidence.

A Capability score based on one benchmark and a Capability score based on eleven benchmarks do not share the same evidence profile, even when both are represented on a 0–100 scale.

Required rule:

```text
Only scores with the same comparison profile, score scale,
anchor definitions, edition, and formula may be ranked together.
```

## 2.3 Model identity is too simplistic for composite services

The current identity model uses a Boolean concept similar to:

```text
fallback_absent: true | false
```

This cannot accurately represent modern deployable AI services that may include:

* Adaptive reasoning.
* Routing.
* Fallback models.
* Multiple service tiers.
* Provider-specific endpoints.
* Composite products.

Claude Fable 5 Max should not be forced into either:

```text
pure Fable with fallback absent
```

or:

```text
reject every observation
```

If the publicly sold product includes a documented fallback policy, that product must be modeled as a composite deployable system configuration.

## 2.4 Current five-model percentile normalization is not a durable UMI scale

Small-cohort percentile fallback effectively assigns ranks such as:

```text
0, 25, 50, 75, 100
```

That destroys magnitude information and makes scores depend on the selected cohort.

A model must not become “100” merely because it is best among five pilot configurations.

Headline v0.4 scores must be normalized against frozen, broader public reference panels.

## 2.5 Public evidence can support a real five-model score

The public score should be constructed from frozen public evidence such as:

* LiveBench task-level public results and resource/cost artifacts.
* DeepSWE public task, attempt, resource, timing, and cost evidence.
* CursorBench public capability, token, step, and task-cost evidence.
* Artificial Analysis public benchmark and service-performance facts.
* Epoch public benchmark matrices where exact compatible rows exist.
* Official public provider tariffs.
* Other public primary benchmark artifacts discovered during implementation.

The project does not need paid benchmark runs merely to publish an informative public score.

---

# 3. Product Architecture

Create two explicitly separate products.

## 3.1 Product A: UMI Public

This is the public headline score for all five pilot configurations.

Use only frozen, public, reproducible evidence.

Target formula:

```text
UMI Public
    = 0.55 × Capability
    + 0.25 × Operational Efficiency
    + 0.20 × Access Economics
```

The component names must be exactly clear in documentation and outputs:

```text
Capability
Operational Efficiency
Access Economics
UMI Public
```

Do not call Access Economics “observed billing economics.”

## 3.2 Product B: UMI Controlled Certificate

Preserve the existing controlled operational ledger architecture as an optional future product.

Controlled evidence may include:

* Exact attempt ledgers.
* Exact endpoint identity.
* Provider billing records.
* Controlled task cohorts.
* Repeated benchmark executions.
* Exact request and response artifacts.

The controlled product must not block publication of UMI Public.

Do not remove the controlled OpenRouter runner. Move it conceptually into the optional controlled verification track and ensure it is not presented as required for UMI Public.

## 3.3 Evidence classes

Introduce explicit evidence classes, for example:

```text
capability
operational_efficiency
access_economics
controlled_economics
diagnostic
vendor_claim
preference
```

For monetary evidence, introduce an explicit enum similar to:

```text
provider_billing_record
benchmark_measured_and_calculated
token_tariff_model
fixed_tariff_basket
source_reported
unknown
```

Rules:

```text
provider_billing_record
    -> may enter UMI Controlled economics

benchmark_measured_and_calculated
token_tariff_model
fixed_tariff_basket
source_reported
    -> may enter UMI Public Access Economics when otherwise ready

unknown
    -> diagnostic only
```

Never silently promote modeled cost into controlled provider-billed economics.

---

# 4. Edition and Versioning Architecture

Do not mutate v0.3 into v0.4 in place.

Create a versioned edition structure. Adapt the exact directory names to the current architecture, but preserve the conceptual separation.

Suggested layout:

```text
config/
  editions/
    v0.3/
    v0.4/

data/
  editions/
    v0.3/
      raw/
      processed/
    v0.4/
      raw/
      processed/
      sources/

docs/
  editions/
    v0.4/
      METHODOLOGY.md
      SOURCE_POLICY.md
      PUBLICATION_POLICY.md
      REPRODUCIBILITY.md
      RESEARCH_NOTES.md

certificates/
  v0.4/

schemas/
  editions/
    v0.4/
```

If moving v0.3 files would break existing paths, preserve compatibility through aliases, loader support, or legacy directories.

Every output must bind:

```text
edition_id
formula_version
normalization_version
engine_version
package_version
config_fingerprint
scored_data_fingerprint
complete_data_fingerprint
comparison_profile_id
score_scale_ids
source_artifact_ids
```

---

# 5. Target UMI Public Contract

## 5.1 Overall weights

Use:

```yaml
overall:
  capability: 0.55
  operational_efficiency: 0.25
  access_economics: 0.20
```

Do not silently change these weights.

Any future alteration requires a new formula version and edition decision record.

## 5.2 Capability domain weights

Use this initial domain structure:

```yaml
capability_domains:
  general_reasoning_and_knowledge: 0.20
  software_engineering: 0.25
  agentic_and_tool_mediated_work: 0.20
  mathematics_and_science: 0.15
  context_reliability_and_factual_discipline: 0.10
  language_data_and_instruction_following: 0.10
```

The domain weights sum to 1.0.

Each positive-weight domain must contain at least one positive-weight common-core family.

Do not reallocate a missing domain’s weight at scoring time.

If a domain lacks exact public common evidence for all five pilots, find an alternative high-quality public source. If no qualifying source exists, the headline must remain unavailable rather than silently reweighting.

## 5.3 Operational Efficiency subcomponents

Use this initial structure:

```yaml
operational_efficiency:
  task_resource_intensity: 0.45
  task_completion_time_and_steps: 0.30
  interactive_service_responsiveness: 0.25
```

Candidate evidence:

```text
task_resource_intensity:
  DeepSWE tokens and cached-token observations
  CursorBench tokens per task
  LiveBench public resource fields
  other exact common public task-resource series

task_completion_time_and_steps:
  DeepSWE wall duration and agent steps
  CursorBench steps per task
  other public common task-duration or tool-step evidence

interactive_service_responsiveness:
  standardized Artificial Analysis output speed
  time to first token
  end-to-end response time
  exact provider/endpoint/service-tier public performance observations
```

Do not compare raw token totals across unrelated tokenizers as though every token represents an identical amount of text.

Normalize operational metrics within compatible source/harness cohorts.

Where possible, preserve tokenizer-independent measures such as bytes or characters as additional diagnostics.

## 5.4 Access Economics subcomponents

Use this initial structure:

```yaml
access_economics:
  public_benchmark_task_cost: 0.45
  agentic_task_cost: 0.30
  fixed_tariff_baskets: 0.25
```

Candidate evidence:

```text
public_benchmark_task_cost:
  LiveBench modeled cost per task or successful task
  CursorBench public task cost
  Artificial Analysis public task cost
  other exact common public benchmark cost evidence

agentic_task_cost:
  DeepSWE cost where observation denominators are complete
  public agentic benchmark cost series
  task-level cost series from comparable agent harnesses

fixed_tariff_baskets:
  official public input/output/cache/tool tariffs
  deterministic fixed usage scenarios
```

If the Fable DeepSWE cost observations remain incomplete relative to its scored attempts, do not silently use that value as a complete all-attempt cost series.

Options are:

1. Keep the incomplete DeepSWE cost diagnostic only.
2. Use a clearly defined complete-observation subset only if the source supports a valid like-for-like common cohort for all five models.
3. Fill the subcomponent using a different exact public all-five source.

Do not impute the missing DeepSWE cost observations.

## 5.5 Source concentration cap

No single evaluator, organization, or strongly correlated source family may provide more than:

```text
35% of the effective weight of any UMI Public component
```

Implement this as a configuration invariant and output diagnostic.

Track:

```text
effective source weight
maximum source share
source-level Herfindahl concentration
leave-one-source-out score movement
```

Correlated task columns from one benchmark do not count as independent source organizations.

## 5.6 Full common-core rule

The first UMI Public edition must use a fixed required common core.

Headline behavior:

```text
required common-core coverage = 100%
```

Do not renormalize missing required evidence.

If one pilot lacks a required common-core series:

```text
headline UMI Public = null
publication state = insufficient_common_support
```

Optional or sparse evidence may be retained diagnostically, but it must not enter the first headline score unless it is available under the same compatible scoring profile for all five pilots.

This prevents incomparable model-specific evidence profiles.

---

# 6. Model and Deployment Identity Rewrite

## 6.1 Replace the fallback Boolean with structured identity

Introduce a structured system-identity model similar to:

```yaml
entity_kind:
  - single_model_service
  - fallback_composite_service
  - router_composite_service
  - open_weight_deployment

model_identity:
  developer:
  named_release:
  revision:
  release_date:
  effort_setting:
  reasoning_mode:

deployment_identity:
  serving_provider:
  endpoint_id:
  service_tier:
  region:
  interface:
  harness:
  scaffold:

routing_policy:
  primary_target:
  fallback_targets:
  route_scope:
  fallback_trigger:
  route_rate:
  route_rate_evidence:
  run_level_routes_available:
```

Adapt names to the existing Pydantic style.

## 6.2 Identity readiness rules

A measurement is scoring-ready only when:

* [ ] The exact named product or model release is known.
* [ ] The effort/reasoning mode is known or explicitly part of the default configuration.
* [ ] The provider and endpoint are compatible with the scored entity.
* [ ] The service tier is compatible when it materially changes latency, cost, or behavior.
* [ ] The harness and scaffold are compatible.
* [ ] A composite service is attributed to the composite product rather than falsely attributed to its underlying primary model.
* [ ] A pure model result is not merged with a fallback-enabled product result.
* [ ] A default-effort result is not silently labeled “Max.”
* [ ] Router-level results are not silently relabeled as first-party endpoint results.
* [ ] Any unresolved identity mismatch remains diagnostic or rejected.

## 6.3 Fable handling

Model the publicly available Fable service truthfully.

If a source evaluates:

```text
Claude Fable 5 Max with documented Opus fallback
```

then score it only against the canonical composite Fable service entity.

Do not require `fallback_absent=true` for the composite product.

Do not use that same evidence for a hypothetical pure-Fable entity.

## 6.4 Kimi and GLM effort handling

Audit every source crosswalk for Kimi K3 and GLM-5.2.

Do not assume:

```text
Kimi K3 == Kimi K3 Max
GLM-5.2 == GLM-5.2 Max
```

The source must prove the effort or configuration.

Where the source publishes only a default configuration:

* Either score the exact default configuration.
* Or provide documented evidence that the default corresponds to the pilot’s canonical Max configuration.
* Otherwise retain the row diagnostically.

## 6.5 Remove release-window validity coupling

A model’s release date should not determine whether valid current evidence can score.

Replace the release-window scoring gate with:

```text
edition cohort manifest
evidence snapshot cutoff
maximum evidence age
series-specific freshness policy
```

The five pilots belong to v0.4 because the edition manifest includes them.

Preserve release dates as metadata and for historical filtering, not as a primary readiness requirement.

---

# 7. Static Policy-Feasibility Validation

Implement configuration validation that proves a scoring edition can theoretically satisfy its own publication gates.

At minimum, calculate:

```python
max_category_coverage = sum(
    category_weight
    for category, category_weight in workload_weights.items()
    if category_has_positive_weight_family(category)
)
```

Add equivalent checks for domains, families, subcomponents, and metrics.

Required validation failures include:

* [ ] A positive-weight category with no positive-weight family.
* [ ] A positive-weight family with no workload or series.
* [ ] A publication threshold above the theoretical maximum attainable coverage.
* [ ] A positive-weight domain with no common-core family.
* [ ] A source-cap configuration that makes the required weights impossible.
* [ ] A family or metric referenced by weight config but absent from the registry.
* [ ] A diagnostic or zero-weight family being counted toward headline coverage.
* [ ] An impossible sensitivity weight set.
* [ ] A required series without an anchor-scale definition.
* [ ] A required common series that does not contain all pilot entities.

Add clear typed validation errors with calculated values.

Example:

```text
edition v0.4 is infeasible:
operational_efficiency maximum attainable category coverage is 0.35,
but publication threshold is 0.50
```

Add regression tests specifically proving that the old impossible configuration is detected when treated as a new edition.

Do not retroactively cause the frozen legacy v0.3 edition to fail ordinary reproducibility builds. Legacy editions may load under an explicit legacy policy mode.

---

# 8. Scoring Trust-Boundary Fixes

## 8.1 Governed scoring API

The normal public API must require the governed bundle.

Preferred API:

```python
score_bundle(...)
```

The unchecked dataset scorer should be private or explicitly marked testing-only:

```python
_score_dataset_unchecked(...)
```

For real, non-synthetic data, the unchecked path must fail unless an explicit unsafe testing flag is supplied.

Do not allow production code to bypass:

* Source registry.
* Checksums.
* Exact crosswalk.
* Acceptance manifest.
* Edition config.
* Signal registry.
* Scoring disposition.
* Readiness validation.

## 8.2 Centralize eligibility

Remove duplicate eligibility implementations.

Create one typed decision object, for example:

```python
EligibilityDecision(
    eligible=False,
    reason_codes=(
        "required_common_series_missing",
        "source_concentration_exceeded",
    ),
    details={...},
)
```

All of the following must consume the same decision:

* CLI.
* Certificates.
* Dashboard.
* Reports.
* Tests.
* Publication output.

## 8.3 Comparison profile identity

Every score must carry a comparison identity similar to:

```text
edition_id
comparison_profile_id
score_scale_id
anchor_panel_ids
formula_version
normalization_version
required_series_ids
```

Ranking code must reject mixed profiles.

Add tests proving that:

* [ ] Partial Capability scores with different evidence profiles cannot be ranked.
* [ ] A dashboard cannot place incomparable partial values in one ordinal chart.
* [ ] Two scores from different normalization versions cannot be ranked as though identical.
* [ ] Display filtering does not refit or change another model’s score.

## 8.4 Deduplicate evidence records

Review Efficiency, Economics, Capability, confidence, and provenance aggregation.

A record populated with multiple metrics must not be counted multiple times merely because it contributes tokens, steps, duration, and cost.

Use unique record IDs when calculating:

* Evidence counts.
* Independent/community evidence share.
* Source organization count.
* Confidence.
* Source concentration.
* Diagnostics.

## 8.5 Separate component confidence from Overall eligibility

Publish independently:

```text
capability_confidence
operational_efficiency_confidence
access_economics_confidence
overall_eligibility
overall_confidence
```

Do not force Capability confidence to Low simply because Access Economics is missing.

## 8.6 Fix evidence freshness semantics

Do not represent the entire score as fresh merely because one contributing source is recent.

Publish:

```text
publication_generated_at
evidence_oldest_as_of
evidence_latest_as_of

capability_oldest_as_of
capability_latest_as_of

operational_oldest_as_of
operational_latest_as_of

access_economics_oldest_as_of
access_economics_latest_as_of
```

Freshness gates should operate on the materially contributing evidence, not only the newest record.

## 8.7 Fix coverage terminology

Use distinct terms with explicit denominators:

```text
categories_represented
families_represented
workloads_represented
series_represented
metric_slots_observed

weighted_category_coverage
weighted_family_coverage
weighted_series_coverage
weighted_metric_coverage
```

Do not label category counts as workload counts.

## 8.8 Zero-weight diagnostic isolation

Separate positive-weight scoring definitions from legacy or diagnostic signals.

Zero-weight families must not influence:

* Headline coverage.
* Domain breadth.
* Confidence.
* Source diversity.
* Gap denominators.
* Eligibility.
* Ranking.

Diagnostic evidence should remain visible in a separate report.

## 8.9 Review inert configuration fields

Audit fields such as any existing family `cap` value.

If a required policy field is not actually used:

* Remove it in the v0.4 schema, or
* Implement and test its semantics.

Do not preserve required but inert policy fields.

---

# 9. Public Source Research and Acquisition

## 9.1 Research policy

Use primary or authoritative sources wherever possible.

Prioritize:

1. Official benchmark repositories.
2. Official public datasets.
3. Official leaderboard data exports.
4. Official methodology pages.
5. Frozen upstream raw artifacts.
6. Reviewed public fact extracts only when raw data is unavailable.
7. Secondary summaries only as research leads, not as scoring sources.

Document all research in:

```text
docs/editions/v0.4/RESEARCH_NOTES.md
```

For every candidate source, record:

```text
source name
official URL
repository URL
data URL
license
redistribution status
retrieval date
revision or commit
available pilot rows
available anchor rows
exact model labels
effort labels
provider and endpoint identity
benchmark version
harness version
task count
trial count
uncertainty availability
candidate UMI role
accept/reject decision
reason
```

## 9.2 Candidate sources to examine

### LiveBench

```text
https://github.com/LiveBench/LiveBench
https://livebench.ai/
```

Requirements:

* Freeze task-level scores.
* Freeze resource/cost artifacts where publicly available.
* Freeze model-answer or judgment artifacts only when licensing permits.
* Freeze category definitions.
* Record exact source revision and checksum.
* Detect files that update in place under the same nominal release name.
* Do not score LiveBench Overall, category aggregates, and individual tasks simultaneously.
* Use task-level series as primary evidence.
* Derive category and overall displays locally.
* Treat all LiveBench tasks as one correlated source family for source-budget purposes.

### DeepSWE

```text
https://deepswe.datacurve.ai/
```

Requirements:

* Reuse and extend the existing trial-ledger verification architecture.
* Preserve exact attempt and success counts.
* Preserve per-metric observation denominators.
* Preserve run counts.
* Preserve model-serving providers.
* Preserve tokens, cached tokens, duration, steps, and cost where complete.
* Do not treat incomplete Fable cost observations as complete.
* Use public capability and operational evidence where exact identity is valid.

### CursorBench

```text
https://cursor.com/cursorbench
```

Requirements:

* Preserve capability score.
* Preserve tokens per task.
* Preserve steps per task.
* Preserve task-cost figures.
* Preserve the source warning regarding variance.
* Record missing task-count and aggregation disclosures.
* Assign reduced evidence confidence where methodology is incomplete.
* Treat CursorBench capability and operational values as one correlated source family.
* Model fallback-enabled Fable as the composite product when the source supports that identity.

### Artificial Analysis

```text
https://artificialanalysis.ai/
https://artificialanalysis.ai/methodology
```

Requirements:

* Freeze exact public benchmark facts.
* Freeze exact provider/endpoint/service-tier performance facts.
* Record prompt length and concurrency/load scenario.
* Record output speed.
* Record time to first token or answer token.
* Record end-to-end response time.
* Record public price and task-cost calculations where methodology is exact.
* Do not import the Artificial Analysis composite Intelligence Index if its constituent benchmarks are already scored.
* Treat multiple AA benchmarks as correlated at the source-organization level.
* Do not allow AA to exceed the source concentration cap.

### Epoch ECI and public benchmark data

```text
https://github.com/epoch-research/eci-public
https://epoch.ai/data/benchmark_data.zip
```

Requirements:

* Use public benchmark matrices as candidate source or anchor evidence when exact configurations are available.
* Do not automatically import the ECI score itself as UMI Capability.
* Do not double-count ECI plus the benchmark rows used to construct ECI.
* Use Epoch’s public IRT implementation as methodological research.
* Preserve exact benchmark, model, and source provenance.
* Reject highest-across-incompatible-settings aggregation when it destroys configuration comparability.

### The Aggregate

```text
https://theaggregate.ai/
```

Use as architectural research into large sparse benchmark matrices and latent scales.

Do not use opaque aggregate scores as UMI evidence without exact public provenance.

Do not introduce missing-value imputation into the first v0.4 headline score.

## 9.3 Mutable-source handling

Every acquisition script must:

* [ ] Require `--accept-network`.
* [ ] Require or generate a unique snapshot ID.
* [ ] Refuse to overwrite an existing snapshot.
* [ ] Save exact raw bytes when redistribution is allowed.
* [ ] Save SHA-256.
* [ ] Save retrieval timestamp.
* [ ] Save source URL.
* [ ] Save ETag and Last-Modified when available.
* [ ] Save upstream commit/revision when available.
* [ ] Save license and attribution.
* [ ] Detect changed bytes under an existing nominal source version.
* [ ] Require a new artifact ID for changed bytes.
* [ ] Never fetch data during scoring.

If redistribution rights are unclear:

* Preserve checksum, URL, revision, and acquisition instructions.
* Commit only reviewed extracted facts when legally appropriate.
* Document the limitation in `SOURCES_AND_LICENSES.md`.

---

# 10. Common-Core Series Selection

Create a committed v0.4 common-core manifest.

Suggested path:

```text
config/editions/v0.4/common-core.yaml
```

A series is headline-eligible only if:

* [ ] It has an exact compatible observation for all five pilot entities.
* [ ] All five observations use the same benchmark version.
* [ ] All five observations use a compatible harness and cohort.
* [ ] All five observations use compatible scoring semantics.
* [ ] All five observations have valid source artifacts.
* [ ] All five observations pass identity readiness.
* [ ] The source license/provenance permits the committed artifact or reviewed facts.
* [ ] The reference anchor panel contains at least eight compatible model configurations.
* [ ] The series has a positive-weight domain or subcomponent assignment.
* [ ] It is not a duplicate of an aggregate already represented by its constituent series.
* [ ] It has a correlation-group ID.
* [ ] It does not cause source concentration to exceed the configured cap.

Preferred minimum anchor panel:

```text
at least 8 exact configurations
target 20 or more when available
```

Do not use five-model rank percentiles as the headline scale.

If a candidate series fails the common-core gate, preserve it as diagnostic evidence with an explicit reason.

---

# 11. Frozen Anchor Normalization

## 11.1 Principle

Every headline series must be normalized against a frozen, broader reference panel.

Scores must not depend on which pilot models are visible in a report.

## 11.2 Required transforms

Use a direction-aware, series-specific transform.

Suggested rules:

### Bounded proportions or accuracy

When a chance baseline is known:

```text
adjusted = (raw - chance) / (1 - chance)
```

Then clamp using a declared epsilon and apply a logit transform.

When the denominator is known, epsilon may use a denominator-aware rule.

When the denominator is unknown, use a fixed declared epsilon such as:

```text
1e-3
```

Record the exact transform in the score-scale artifact.

### Positive cost, latency, token, duration, or step metrics

Use:

```text
log(raw)
```

Then invert direction because lower is better.

Handle zero values only through an explicitly configured offset justified by the metric.

### Elo or unbounded scores

Use identity or another explicitly justified monotonic transform.

Do not mix raw units directly.

## 11.3 Robust reference normalization

For every transformed series:

```text
median = anchor-panel median
mad = median absolute deviation
robust_sigma = 1.4826 × mad
robust_z = (value - median) / robust_sigma
```

Winsorize robust z using a configured range, initially:

```text
[-3, 3]
```

Map to 0–100 using:

```text
series_score = 100 × standard_normal_cdf(robust_z)
```

Properties:

```text
approximately 50 = reference-panel median
approximately 84 = one robust standard deviation above median
approximately 16 = one robust standard deviation below median
```

## 11.4 Fail-closed normalization

For headline scoring:

* Do not use percentile fallback when the anchor panel is too small.
* Do not use a five-model display cohort as the anchor panel.
* If anchor count is below the configured minimum, the series is ineligible.
* If MAD is zero, use a documented robust fallback such as IQR only when mathematically valid.
* If no stable scale can be constructed, the series is ineligible.
* Record every transform, anchor ID, anchor member, and reference statistic.

## 11.5 Display invariance test

Add a mandatory regression test:

```text
Removing, hiding, or reordering a display model must not change
the published score of any other model.
```

Also test:

* Adding a non-pilot display row changes no existing score.
* Reordering input rows changes no score.
* Rebuilding from the same artifacts is byte-deterministic.
* A new reference panel requires a new normalization version.

---

# 12. Weighting and Correlation Control

## 12.1 Do not weight by column count

A benchmark with 23 task columns must not receive 23 times the influence of a benchmark with one published score.

Use hierarchical budgets:

```text
component
  -> domain or subcomponent
    -> benchmark family
      -> source/correlation group
        -> series
```

Weights must be declared at the appropriate policy level.

## 12.2 Correlation groups

Add explicit correlation-group IDs.

Examples:

```text
livebench-current-release
deepswe-v1.1-four-run-cohort
cursorbench-3.2
aa-intelligence-v4.1.1
epoch-simple-evals-gpqa
official-provider-tariffs
```

Series in one correlation group must:

* Share a family budget.
* Be resampled together during source-level uncertainty.
* Count as one correlated source group for concentration diagnostics.

## 12.3 No aggregate plus constituents

Do not simultaneously score:

* LiveBench Overall and LiveBench tasks.
* LiveBench category averages and the same task rows.
* Artificial Analysis Intelligence Index and the same constituent benchmarks.
* Epoch ECI and the same constituent benchmark matrix.
* Pass@1 and a deterministic aggregate derived from the same pass@1 values unless the edition explicitly treats one as diagnostic.
* Capability score, cost score, and token score from the same row as independent source organizations.

The values may enter different components when conceptually appropriate, but their common source correlation must remain visible and included in uncertainty.

---

# 13. Missing Data Policy

For UMI Public v0.4 headline scoring:

```text
no imputation
no missing-series reweighting
no nearest-model substitution
no vendor-claim substitution
no hidden fallback substitution
```

If a required common series is missing:

```text
headline_overall = null
status = insufficient_common_support
```

Optional diagnostic values may be shown separately.

Do not use a latent missing-value model in the first public release.

Create a future research note for possible v0.5 sparse-matrix or IRT work, but do not let that delay or contaminate v0.4.

---

# 14. Uncertainty and Rank Robustness

## 14.1 Replace endpoint-only uncertainty as the primary method

Retain deterministic endpoint analysis as a diagnostic adversarial bound if useful.

Add a primary hierarchical/bootstrap uncertainty implementation.

## 14.2 Source-specific uncertainty

Use, in order of preference:

1. Raw task or attempt bootstrap.
2. Whole-run bootstrap.
3. Source-published confidence interval.
4. Binomial or denominator-aware interval when mathematically justified.
5. Conservative source-unknown uncertainty policy.
6. Diagnostic-only status when no defensible uncertainty can be constructed.

Do not assume zero uncertainty merely because the source publishes only a point estimate.

## 14.3 Hierarchical resampling

Preserve correlation among observations from the same source or harness.

A recommended draw process:

1. Sample task or attempt outcomes within each benchmark where raw evidence exists.
2. Sample run-level results where repeated runs exist.
3. Sample source-provided score distributions where only intervals exist.
4. Resample benchmark families or correlation groups.
5. Apply configured weight-sensitivity draws.
6. Recompute normalized series, components, and Overall.
7. Repeat with a deterministic seed.

Use a sufficient number of draws, such as:

```text
10,000 default publication draws
```

Allow a smaller test setting for CI.

## 14.4 Publish

For each model:

```text
central UMI Public score
95% interval
component scores
component intervals
source-ablation range
weight-sensitivity range
oldest and newest evidence dates
```

For pairwise comparisons:

```text
P(model A > model B)
central score difference
difference interval
rank range
robust dominance status
```

Where scores are not statistically distinguishable, render them as ties or near-ties rather than assigning false precision.

## 14.5 Determinism

Every uncertainty output must bind:

```text
seed
draw count
resampling method version
correlation groups
weight scenario definition
```

Repeated runs with identical inputs must produce identical outputs.

---

# 15. Dashboard and Reporting

Do not prioritize cosmetic work before the scoring pipeline is correct.

After the canonical v0.4 JSON artifacts exist, update or extend the dashboard.

## 15.1 Required dashboard behavior

Display:

* UMI Public score.
* 95% interval.
* Capability.
* Operational Efficiency.
* Access Economics.
* Exact system configuration.
* Entity kind.
* Provider and service identity.
* Composite/fallback status.
* Evidence coverage.
* Source concentration.
* Data-as-of range.
* Rank range.
* Pairwise indistinguishability or tie status.
* Major limitations.
* Certificate link or identifier.

## 15.2 Prohibited dashboard behavior

Do not:

* Render unavailable values as zero.
* Rank partial values with full common-core values.
* Hide modeled-cost labels.
* Present Access Economics as provider-billed economics.
* Recompute scores in JavaScript or HTML.
* Create a separate formula in the dashboard.
* Display excessive decimal precision.
* Rank statistically indistinguishable models without qualification.

The dashboard must consume canonical processed JSON generated by the Python scoring engine.

---

# 16. Required Code Defects to Audit and Fix

Audit current code rather than assuming exact line numbers.

Likely affected areas include:

```text
umi/scoring.py
umi/capability.py
umi/efficiency.py
umi/economics.py
umi/readiness.py
umi/schemas.py
umi/config.py
umi/loading.py
umi/bundle.py
umi/__init__.py

analysis/compare.py
analysis/gaps.py
analysis/pilot_dashboard.py
analysis/uncertainty.py
analysis/rankings.py
analysis/sensitivity.py

config/eligibility.yaml
config/workloads.yaml
config/weights.yaml
config/benchmarks.yaml
config/normalization.yaml

scripts/build_v03_pilot.py
CLI command modules
schema-generation modules
tests/
```

Required fixes:

* [ ] Add policy-feasibility validation.
* [ ] Prevent impossible editions from passing config validation.
* [ ] Make governed scoring the public/default API.
* [ ] Restrict unchecked scoring to synthetic/testing use.
* [ ] Separate public Access Economics from controlled billed Economics.
* [ ] Remove the typed loophole that lets unverified cost fields enter controlled Economics.
* [ ] Add structured cost-evidence kinds.
* [ ] Add structured deployment and routing identity.
* [ ] Replace simplistic fallback absence logic.
* [ ] Remove release-window coupling from evidence validity.
* [ ] Centralize eligibility.
* [ ] Add comparison profile IDs.
* [ ] Prevent ranking across incompatible profiles.
* [ ] Deduplicate evidence records by record ID.
* [ ] Correct coverage names and denominators.
* [ ] Isolate zero-weight diagnostic families.
* [ ] Separate component confidence from Overall eligibility.
* [ ] Add oldest/latest evidence dates.
* [ ] Add source concentration metrics and gates.
* [ ] Audit inert config fields.
* [ ] Remove unconditional or inaccurate blocker text from gap reports.
* [ ] Ensure diagnostic evidence cannot improve headline coverage or confidence.
* [ ] Ensure generated artifacts are never manually edited.
* [ ] Ensure v0.3 and v0.4 use separate formula and normalization identities.

---

# 17. Execution Phases

Proceed through the following phases continuously.

Do not stop after an intermediate phase unless the repository is genuinely broken in a way that prevents further safe work.

## Phase 0 — Baseline audit

* [ ] Record current branch and `HEAD`.
* [ ] Record `git status`.
* [ ] Inspect package version, formula version, normalization version, and engine version.
* [ ] Run the existing full verification suite.
* [ ] Record current test counts and artifact hashes.
* [ ] Record current v0.3 certificate hashes.
* [ ] Inspect current CI configuration.
* [ ] Search for stubs, dead code, unused policy fields, duplicate logic, and stale documentation.
* [ ] Write:

```text
docs/editions/v0.4/BASELINE_AUDIT.md
```

Suggested baseline commands:

```bash
git status --short
git rev-parse HEAD

uv sync --frozen --extra dev --no-editable

PYTHONPATH=. uv run --no-sync pytest
PYTHONPATH=. uv run --no-sync ruff check .
PYTHONPATH=. uv run --no-sync mypy
git diff --check
```

Use the current repository’s documented verification commands when they differ.

## Phase 1 — Freeze v0.3

* [ ] Preserve the current v0.3 build and outputs.
* [ ] Add golden checksums for legacy processed artifacts.
* [ ] Add a legacy edition identifier.
* [ ] Preserve current CLI compatibility.
* [ ] Add tests proving v0.3 remains byte-identical.
* [ ] Do not apply v0.4 normalization or identity semantics retroactively to v0.3.
* [ ] Commit this phase separately.

Suggested commit:

```text
Freeze v0.3 as immutable legacy edition
```

## Phase 2 — Add edition and feasibility infrastructure

* [ ] Add edition-aware config loading.
* [ ] Add edition-aware schema and artifact metadata.
* [ ] Implement policy-feasibility validation.
* [ ] Add positive-weight hierarchy validation.
* [ ] Add source-cap feasibility validation.
* [ ] Add common-core manifest validation.
* [ ] Add regression tests.
* [ ] Commit this phase separately.

Suggested commit:

```text
Add edition-aware policy feasibility validation
```

## Phase 3 — Rewrite system identity

* [ ] Add structured entity kind.
* [ ] Add structured model identity.
* [ ] Add structured deployment identity.
* [ ] Add routing/fallback policy.
* [ ] Add composite-service readiness rules.
* [ ] Build exact v0.4 pilot entity manifests.
* [ ] Rework Fable identity as appropriate.
* [ ] Audit Kimi and GLM effort identity.
* [ ] Remove release-window validity coupling.
* [ ] Add identity regression tests.
* [ ] Commit this phase separately.

Suggested commit:

```text
Model exact deployable and composite service identity
```

## Phase 4 — Close scoring trust-boundary problems

* [ ] Govern scoring through validated bundles.
* [ ] Privatize unchecked scorer.
* [ ] Centralize eligibility.
* [ ] Add comparison-profile identity.
* [ ] Prevent mixed-profile ranking.
* [ ] Deduplicate evidence.
* [ ] Correct confidence semantics.
* [ ] Correct coverage terminology.
* [ ] Correct evidence freshness semantics.
* [ ] Isolate zero-weight diagnostics.
* [ ] Add tests.
* [ ] Commit this phase separately.

Suggested commit:

```text
Harden scoring comparability and evidence accounting
```

## Phase 5 — Split Access and Controlled Economics

* [ ] Add public cost-evidence schema.
* [ ] Add controlled billing-evidence schema.
* [ ] Prevent public modeled cost from entering controlled Economics.
* [ ] Add deterministic tariff-basket schema.
* [ ] Add Access Economics component.
* [ ] Preserve legacy controlled Economics behavior for v0.3.
* [ ] Add tests.
* [ ] Commit this phase separately.

Suggested commit:

```text
Separate public access cost from controlled billing economics
```

## Phase 6 — Research and freeze public sources

* [ ] Complete source research.
* [ ] Freeze LiveBench.
* [ ] Verify and extend DeepSWE evidence.
* [ ] Freeze CursorBench facts.
* [ ] Freeze Artificial Analysis benchmark and performance facts.
* [ ] Freeze official tariffs.
* [ ] Investigate Epoch and other public anchor panels.
* [ ] Record licenses.
* [ ] Record checksums.
* [ ] Add source registry entries.
* [ ] Add crosswalk entries.
* [ ] Add adapter tests.
* [ ] Commit source snapshots and reviewed facts according to licensing.
* [ ] Commit this phase separately.

Suggested commit:

```text
Freeze v0.4 public benchmark and service evidence
```

## Phase 7 — Build the common core and anchor scales

* [ ] Create common-core manifest.
* [ ] Verify all five pilot cells.
* [ ] Create domain/family/source budgets.
* [ ] Create anchor panels.
* [ ] Implement robust transforms.
* [ ] Implement robust z normalization.
* [ ] Implement standard-normal CDF mapping.
* [ ] Remove percentile fallback from v0.4 headline scoring.
* [ ] Add display-invariance tests.
* [ ] Add anchor mutation tests.
* [ ] Add source-cap tests.
* [ ] Commit this phase separately.

Suggested commit:

```text
Add frozen public anchor scales and common-core scoring
```

## Phase 8 — Implement UMI Public components

* [ ] Build Capability.
* [ ] Build Operational Efficiency.
* [ ] Build Access Economics.
* [ ] Build Overall UMI Public.
* [ ] Require full common-core support.
* [ ] Add per-component certificates.
* [ ] Add overall certificates.
* [ ] Add raw contribution artifacts.
* [ ] Add score-scale artifacts.
* [ ] Add source-concentration artifacts.
* [ ] Add full deterministic build.
* [ ] Commit this phase separately.

Suggested commit:

```text
Implement five-model UMI Public scoring
```

## Phase 9 — Implement uncertainty and sensitivity

* [ ] Add task/run/source hierarchical bootstrap.
* [ ] Add source interval support.
* [ ] Add correlation groups.
* [ ] Add weight sensitivity.
* [ ] Add source ablation.
* [ ] Add rank probability and range.
* [ ] Add tie handling.
* [ ] Add deterministic seed and draw metadata.
* [ ] Add reduced-draw CI tests.
* [ ] Commit this phase separately.

Suggested commit:

```text
Add hierarchical uncertainty and robust rank reporting
```

## Phase 10 — Documentation and dashboard

* [ ] Rewrite the README around UMI Public.
* [ ] Update METHODOLOGY.
* [ ] Update DATA_SCHEMA.
* [ ] Update SOURCE_READINESS.
* [ ] Update SOURCES_AND_LICENSES.
* [ ] Update VERIFICATION.
* [ ] Update BUILD_PLAN.
* [ ] Update ADVERSARIAL_REVIEW.
* [ ] Clearly de-emphasize paid runs as optional Controlled certification.
* [ ] Build v0.4 dashboard from canonical JSON.
* [ ] Add documentation tests where practical.
* [ ] Commit this phase separately.

Suggested commit:

```text
Publish UMI Public methodology, certificates, and dashboard
```

## Phase 11 — Final verification

* [ ] Run every existing test.
* [ ] Run every new test.
* [ ] Run Ruff.
* [ ] Run mypy.
* [ ] Run schema generation.
* [ ] Rebuild v0.3 and compare hashes.
* [ ] Rebuild v0.4 twice and compare hashes.
* [ ] Build the wheel.
* [ ] Install the wheel outside the repository.
* [ ] Run CLI smoke tests from the installed package.
* [ ] Run `git diff --check`.
* [ ] Confirm no generated artifact drift.
* [ ] Confirm no network access occurs during scoring.
* [ ] Confirm no API key is required.
* [ ] Confirm no paid request path ran.
* [ ] Confirm all five pilot certificates exist.
* [ ] Commit final verification artifacts.

Suggested commit:

```text
Verify reproducible five-model UMI Public release
```

---

# 18. Required Tests

At minimum, add tests for the following.

## 18.1 Policy feasibility

* [ ] Impossible maximum coverage fails.
* [ ] Positive-weight category without families fails.
* [ ] Positive-weight family without series fails.
* [ ] Source-cap infeasibility fails.
* [ ] Required common series lacking one pilot fails.
* [ ] Zero-weight diagnostics do not satisfy coverage.

## 18.2 Identity

* [ ] Pure model and composite service cannot merge.
* [ ] Fable composite evidence scores only for the composite entity.
* [ ] Fable composite evidence does not score for a pure-Fable entity.
* [ ] Unknown effort cannot map to Max.
* [ ] Endpoint mismatch fails.
* [ ] Provider mismatch fails when material.
* [ ] Service-tier mismatch fails when material.
* [ ] Router result cannot silently become first-party result.

## 18.3 Economics

* [ ] Modeled task cost cannot enter controlled Economics.
* [ ] Provider billing cannot silently become tariff-modeled cost.
* [ ] Incomplete observation denominators remain incomplete.
* [ ] Cache reads and writes are handled.
* [ ] Tool fees are handled.
* [ ] Long-context surcharges are handled.
* [ ] Fixed baskets reproduce exactly from frozen tariffs.

## 18.4 Comparability

* [ ] Different comparison profiles cannot be ranked.
* [ ] Different scale versions cannot be ranked.
* [ ] Partial and headline scores cannot share one rank list.
* [ ] Hiding a model changes no score.
* [ ] Reordering data changes no score.
* [ ] Duplicate records change no score.
* [ ] Extra populated metric fields do not inflate confidence.

## 18.5 Source weighting

* [ ] One source cannot exceed 35% effective component weight.
* [ ] Twenty-three LiveBench tasks remain within one source budget.
* [ ] Aggregate plus constituent double-counting is rejected.
* [ ] Correlation groups are resampled together.

## 18.6 Uncertainty

* [ ] Identical seed produces identical draws.
* [ ] Wider source uncertainty cannot produce a narrower overall interval.
* [ ] Source ablation is deterministic.
* [ ] Pairwise probabilities are internally consistent.
* [ ] Ties or indistinguishable scores render correctly.
* [ ] No arbitrary method switch occurs at a small record-count boundary.

## 18.7 Versioning and reproducibility

* [ ] v0.3 artifacts remain byte-identical.
* [ ] v0.4 rebuilds are byte-identical.
* [ ] Package version, formula version, and normalization version are distinct.
* [ ] Changing an anchor panel requires a new scale version.
* [ ] Changing source bytes changes the complete fingerprint.
* [ ] Changing a scored source changes the scored fingerprint.
* [ ] Diagnostic-only changes do not silently change the score.
* [ ] Scoring performs no network access.

---

# 19. Proposed CLI

Adapt to the current CLI style while retaining backward compatibility.

Preferred commands:

```bash
umi edition validate --edition v0.4

umi edition build --edition v0.4

umi edition score --edition v0.4

umi edition certificate --edition v0.4 --all

umi edition sources validate --edition v0.4 --strict

umi edition crosswalk validate --edition v0.4

umi edition anchors validate --edition v0.4

umi edition uncertainty --edition v0.4

umi edition dashboard --edition v0.4
```

Acquisition commands must be explicit and separate:

```bash
python -m scripts.freeze_v04_livebench \
  --accept-network \
  --snapshot-id SNAPSHOT_ID

python -m scripts.freeze_v04_public_performance \
  --accept-network \
  --snapshot-id SNAPSHOT_ID

python -m scripts.freeze_v04_tariffs \
  --accept-network \
  --snapshot-id SNAPSHOT_ID
```

If the existing acquisition framework is extensible, add source plugins rather than duplicating infrastructure.

Scoring commands must work offline after acquisition.

---

# 20. Required v0.4 Outputs

Produce canonical machine-readable artifacts similar to:

```text
data/editions/v0.4/processed/edition-manifest.json
data/editions/v0.4/processed/source-readiness.json
data/editions/v0.4/processed/common-core.json
data/editions/v0.4/processed/anchor-panels.json
data/editions/v0.4/processed/score-scales.json
data/editions/v0.4/processed/source-concentration.json
data/editions/v0.4/processed/model-scores.json
data/editions/v0.4/processed/pairwise-comparisons.json
data/editions/v0.4/processed/uncertainty.json
data/editions/v0.4/processed/source-ablation.json
data/editions/v0.4/processed/weight-sensitivity.json
data/editions/v0.4/processed/rejected-evidence.json
data/editions/v0.4/processed/public-dashboard.json
data/editions/v0.4/processed/public-dashboard.html
```

Per-model certificates should contain:

```text
edition ID
canonical model/system ID
entity kind
model identity
deployment identity
routing/fallback identity
UMI Public score
95% interval
Capability score and interval
Operational Efficiency score and interval
Access Economics score and interval
rank or tie group
possible rank range
pairwise superiority probabilities
required common-core coverage
source concentration
source-ablation range
weight-sensitivity range
oldest evidence date
latest evidence date
source record IDs
source artifact IDs
artifact checksums
anchor panel IDs
score scale IDs
comparison profile ID
formula version
normalization version
engine version
package version
config fingerprint
scored data fingerprint
complete data fingerprint
publication state
warnings and limitations
```

---

# 21. Documentation Requirements

Create or update documentation so a technically capable third party can understand and reproduce the score.

## 21.1 README

The README should answer:

* What is UMI Public?
* What is UMI Controlled?
* Why are they separate?
* What do the three public components mean?
* Which five systems are scored?
* What evidence is public?
* How are anchor scales frozen?
* How are costs classified?
* How is uncertainty handled?
* How can a third party rebuild everything?
* What is not claimed?

## 21.2 Methodology

Document exact formulas, including:

```text
raw transform
chance correction
robust normalization
winsorization
CDF mapping
domain weighting
family weighting
source caps
missing-data policy
component aggregation
Overall aggregation
uncertainty
eligibility
tie handling
```

## 21.3 Source documentation

For every scored source, document:

```text
who produced it
what was measured
which exact configurations were measured
what was frozen
when it was frozen
license and redistribution status
what enters Capability
what enters Operational Efficiency
what enters Access Economics
what remains diagnostic
known limitations
```

## 21.4 Limitations

Explicitly state:

* UMI Public uses public evidence rather than controlled private reruns.
* Access Economics includes modeled or source-calculated cost.
* It is not a provider billing audit.
* Public service performance may vary by provider and date.
* Composite products are scored as products.
* A 0–100 UMI score is not a percentage correct.
* Close score intervals may imply no meaningful rank difference.
* A new edition may update sources, anchors, or formula versions.

---

# 22. Non-Negotiable Definition of Done

Do not declare the project complete until all applicable items pass.

* [ ] v0.3 remains reproducible and unchanged.
* [ ] v0.4 has a separate edition identity.
* [ ] The scoring policy is mathematically feasible.
* [ ] All five system configurations have exact identity manifests.
* [ ] Fable is modeled truthfully as a pure or composite product according to public evidence.
* [ ] Kimi and GLM effort mappings are proven rather than assumed.
* [ ] Every required common-core series contains all five pilots.
* [ ] Every headline series has a frozen anchor panel.
* [ ] Every anchor panel contains at least eight compatible configurations.
* [ ] Display-model selection cannot change any score.
* [ ] No source exceeds the 35% component concentration cap.
* [ ] No aggregate and constituent double-counting remains.
* [ ] No modeled cost enters controlled billed Economics.
* [ ] Every public cost value has an explicit evidence kind.
* [ ] Missing required evidence is not imputed or reweighted.
* [ ] All five models have Capability scores.
* [ ] All five models have Operational Efficiency scores.
* [ ] All five models have Access Economics scores.
* [ ] All five models have UMI Public scores.
* [ ] Every score has a 95% interval.
* [ ] Pairwise probabilities and rank ranges are generated.
* [ ] Source ablations are generated.
* [ ] Weight sensitivity is generated.
* [ ] Oldest and newest contributing evidence dates are visible.
* [ ] All source artifacts have checksums.
* [ ] All scored source rows have exact crosswalks.
* [ ] All licenses and attribution requirements are documented.
* [ ] Scoring and rebuilds require no API keys.
* [ ] Scoring and rebuilds perform no network calls.
* [ ] No paid evaluation calls were made.
* [ ] Every existing test passes.
* [ ] Every new test passes.
* [ ] Ruff passes.
* [ ] mypy passes.
* [ ] Wheel build passes.
* [ ] Installed-package CLI smoke tests pass.
* [ ] v0.4 rebuild is byte-deterministic.
* [ ] The public dashboard consumes canonical JSON.
* [ ] No production stubs or placeholders remain.
* [ ] Final implementation report is written.

If genuinely sufficient public evidence cannot be found for one required subcomponent, do not fabricate a score.

Continue implementing every non-data-blocked architectural change and write an exact blocker report containing:

```text
missing series
affected model
required identity
sources investigated
URLs investigated
reason each source failed
what evidence would resolve the blocker
```

However, do not stop at the first missing source. Search for alternate high-quality public evidence before declaring a blocker.

---

# 23. Things You Must Not Do

* Do not lower eligibility gates just to publish.
* Do not reuse the existing partial component scores as UMI Public.
* Do not call a Capability-only certificate an Overall UMI score.
* Do not run the paid MMLU-Pro or OpenRouter pilot.
* Do not treat a public price card as a provider billing ledger.
* Do not treat source-calculated cost as observed billing.
* Do not use vendor release claims as independent measurements.
* Do not count one composite index and all of its constituents.
* Do not count one benchmark’s many task columns as many independent sources.
* Do not force fallback-enabled Fable evidence into a fallback-absent schema.
* Do not label default Kimi or GLM configurations as Max without proof.
* Do not use the five pilots themselves as the permanent normalization panel.
* Do not use percentile fallback for v0.4 headline scores.
* Do not impute missing required pilot cells.
* Do not silently reweight around missing required evidence.
* Do not hide unavailable values by displaying zero.
* Do not publish excessive decimal precision.
* Do not assign rigid ranks to statistically indistinguishable scores.
* Do not add visual polish while scoring defects remain unresolved.
* Do not rewrite or delete the functioning v0.3 controlled architecture.
* Do not introduce a parallel scoring implementation in frontend code.
* Do not claim completion after writing only plans or documentation.

---

# 24. Final Agent Deliverables

At the end of the implementation, create:

```text
IMPLEMENTATION_REPORT_V04.md
```

It must include:

1. Starting commit.
2. Ending commit.
3. Branch name.
4. High-level architecture implemented.
5. Files and modules added.
6. Files and modules materially changed.
7. Data sources accepted.
8. Data sources rejected.
9. Exact five scored system identities.
10. Final common-core manifest.
11. Final anchor-panel strategy.
12. Final component weights.
13. Final source concentration values.
14. Final five Capability scores.
15. Final five Operational Efficiency scores.
16. Final five Access Economics scores.
17. Final five UMI Public scores.
18. Every 95% interval.
19. Rank ranges and ties.
20. Source-ablation findings.
21. Weight-sensitivity findings.
22. Remaining limitations.
23. Full verification commands.
24. Full verification results.
25. Confirmation that no paid requests were made.
26. Confirmation that no API keys are required.
27. Confirmation that v0.3 artifacts remain stable.

The terminal or final agent response should end with a compact status report similar to:

```text
UMI v0.4 IMPLEMENTATION STATUS

Legacy v0.3 reproducibility: PASS/FAIL
Policy feasibility: PASS/FAIL
Five exact system identities: PASS/FAIL
Five-model common core: PASS/FAIL
Frozen anchor scales: PASS/FAIL
Capability component: PASS/FAIL
Operational Efficiency component: PASS/FAIL
Access Economics component: PASS/FAIL
Uncertainty and sensitivity: PASS/FAIL
Five UMI Public certificates: PASS/FAIL
No paid requests: PASS/FAIL
No API keys required: PASS/FAIL
Full test suite: PASS/FAIL
Ruff: PASS/FAIL
mypy: PASS/FAIL
Wheel smoke test: PASS/FAIL
Deterministic rebuild: PASS/FAIL

Final scores:
1. ...
2. ...
3. ...
4. ...
5. ...

Branch:
Commit:
Implementation report:
```

Do not finish with only recommendations. Finish with implemented code, frozen evidence, passing validation, reproducible artifacts, and the real five-model UMI Public result—or an exact, evidence-backed blocker report where publication would otherwise require fabricating evidence.
