# UMI methodology (v0.2-draft)

> **Status:** adversarially hardened pre-ingestion specification. Scores remain
> cohort-relative and experimental. No UMI score is a timeless model property.

This document is authoritative. Code and configuration must not introduce scoring behavior that is absent here.

## Entity, eligibility, and evidence

The unit of analysis is a model configuration, including reasoning effort. The default release window is 2026-06-15 through 2026-08-14. A model may receive partial component scores, but a headline Overall rank requires at least 60% weighted Overall coverage and Capability evidence in at least three domains.

Every measurement requires provenance, including organization, URL, access date, result type, benchmark version, harness when known, model configuration, tools status, and metric definition. Conflicting measurements are preserved. For scoring, use the median of independent measurements when present; otherwise use the median from the first available tier in this order: community reproduction, vendor reported, derived. Emit a conflict diagnostic whenever more than one candidate record exists.

## Normalization

Normalization occurs within a comparable metric, version, workload, and evaluation setting cohort. Scores are relative to that cohort.

For five or more finite observations, apply the configured transform, then compute `z = (x - median) / (1.4826 × MAD)` and map with `100 × NormalCDF(z)`. Log-skewed lower-is-better metrics use `log1p(x)` before normalization. Lower-is-better scores are inverted after transformation. If MAD is zero, use average-rank percentiles.

For two through four observations, use average-rank percentiles and mark the result provisional. A singleton is unscored. A measured zero-success run is the explicit worst outcome for effective cost/tokens, not missing evidence. Scores are rounded only for presentation.

## Capability

Capability has three distinct weight layers: capability-domain weights;
benchmark-family weights within each domain plus an independently configured
maximum family influence (`cap`); and representation weights for benchmark members
within a family. Family weights in a domain sum to one. Effective family influence
is `min(weight, cap)`. Members share one family budget, so aliases, aggregates, and
constituents cannot manufacture additional influence.

Default domain weights are general reasoning 27.5%, software engineering 27.5%, agentic work 20%, math/science 15%, and context/reliability 10%. Benchmark weights are allocated inside each domain.

Benchmark families are weight budgets. An aggregate and its known constituents share a family budget; adding another representation of the same underlying benchmark cannot increase that family's total influence. Within a family, available benchmark weights are renormalized to the configured family budget. Domain caps prevent excess influence. Empirical correlation is diagnostic only in v1.

## Efficiency

Every workload belongs to one configured class: `coding_agents`,
`research_analysis`, `tool_use_agents`, `browser_computer_use`,
`general_interaction`, or `long_horizon`. Metrics are normalized inside a compatible
workload cohort, averaged inside their class, then combined using configured class
weights. Multiple workloads in one class share its budget. Missing classes are
reweighted only for a partial estimate and reduce weighted Efficiency coverage.
UMI does not invent a neutral prior; sparse support remains visible and can prevent
headline eligibility.

The default metric weights are effective tokens per successful task 50%, turns per task 20%, wall-clock seconds per task 20%, and tool calls per task 10%. `EffectiveTokens = MeanTokensPerAttempt / SuccessRate`. Missing metrics are excluded and remaining weights are renormalized; coverage records the omitted weight.

## Economics

Economics uses the same explicit workload classes and class budgets. Costs from
unlike classes are never normalized against each other or interpreted as direct
price ratios. The first real-data pilot must remain narrow when comparable baskets
are unavailable.

`CostPerSuccessfulTask = MeanCostPerAttempt / SuccessRate`. Headline Economics uses comparable observed cost per successful task only. Advertised input, cached-input, output, cache-write, reasoning-token, long-context, and tool pricing are stored and validated but are not converted into a headline score until workload baskets exist.

## Overall, Value, coverage, and confidence

The renormalized diagnostic number is serialized as `partial_overall_estimate`.
`headline_overall` is populated only when eligibility rules pass; otherwise it is
`null`. There is intentionally no ambiguous serialized `overall` field.

Value is **experimental**. Its configured candidates are geometric mean,
weighted geometric mean, and harmonic mean. No candidate is declared correct.
Output identifies the selected formula and Value sensitivity reports score/rank
ranges. A raw-cost formula is deferred until compatible observed-cost baskets
exist.

Confidence is capped at Medium when selected evidence comes from fewer than two
source organizations and at Low when fewer than three Capability domains are
represented. Coverage, cohort size, provisional normalization, conflicts,
vendor-only evidence, sparse workloads, and source diversity are returned as
explicit reasons.

Coverage metadata separately reports weighted Overall coverage, Capability domain
and family coverage, Efficiency and Economics workload-class counts and weighted
coverage, independent/community share, and distinct source organizations.
Measurement count is not evidence breadth.

The default Overall score is `0.55C + 0.25E + 0.20X`. Missing components are renormalized over available component weights; weighted coverage is always reported. Configured sensitivity sets are 55/25/20, 60/20/20, 50/30/20, 60/25/15, and 50/25/25.

Value is separate: `sqrt(Capability × observed-cost-efficiency score)`. It is unavailable without both inputs.

Confidence is High at coverage >=80% and independent/community evidence share >=75%; Medium at coverage >=60% and that evidence share >=50%; otherwise Low. Evidence quality is weighted first by the headline component weight and component coverage; selected records within a component contribute equally in v0.1. Any small-cohort normalization or failed headline eligibility marks the result provisional.

Aggregate/constituent metadata must use the same benchmark-family ID. Validation rejects an overlap declared across different families, ensuring the scoring engine places every known overlap inside one shared family budget.

## Sensitivity, correlation, and Pareto analysis

Sensitivity analysis recomputes scores and reports baseline rank, rank range, score range, maximum rank movement, and stability (`1 - rank_range/(ranked_models-1)`, with one model defined as 1). Correlation output includes Pearson, Spearman, and overlap count; interpretive flags require the configured minimum overlap. Correlation does not alter v1 scores.

A model is Pareto dominated when another model is at least as capable and no more costly/inefficient, with one strict improvement. Equal points do not dominate each other. Outputs name all dominators.

## Cohort identity and evaluation compatibility

Every result records a deterministic cohort ID, sorted cohort model IDs,
evaluation date, normalization version, and configuration fingerprint. Adding or
removing models can change existing scores, even with robust normalization.

Benchmark labels alone never establish comparability. Every measurement carries a
`cohort_key` and model snapshot identifier. The key represents benchmark/harness
versions, scaffold, tools, retry policy, effort, context, pass@k, endpoint snapshot,
and other material settings. Different keys normalize separately and share the
benchmark representation budget. A model ID associated with multiple snapshots is
an error. Optional task/trial/sample counts, standard error, and confidence
interval are preserved but do not yet alter scores.

## Unresolved questions

- How should nominal price baskets vary by workload and context length?
- When is overlap sufficient for empirical correlation-based weight reduction?
- How should formal measurement uncertainty and benchmark sampling error propagate?
- How should heterogeneous workload categories combine without hiding user-specific tradeoffs?
- Should evidence tiers receive calibrated quality weights once validation history exists?
- Should fixed reference cohorts, anchors, or period-specific scales replace fully
  relative cohorts?
- What documented tolerance, if any, should turn near-equal scores into analytical
  ties? Exact ties currently receive average ranks; presentation rounds to one decimal.
- How should sample uncertainty and rank/value sensitivity affect confidence?
- Very low nonzero success remains unclipped; log transforms reduce leverage without
  hiding catastrophic failure, while zero remains explicit worst.
