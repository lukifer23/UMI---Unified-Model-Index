# UMI methodology (v0.1)

This document is authoritative. Code and configuration must not introduce scoring behavior that is absent here.

## Entity, eligibility, and evidence

The unit of analysis is a model configuration, including reasoning effort. The default release window is 2026-06-15 through 2026-08-14. A model may receive partial component scores, but a headline Overall rank requires at least 60% weighted Overall coverage and Capability evidence in at least three domains.

Every measurement requires provenance, including organization, URL, access date, result type, benchmark version, harness when known, model configuration, tools status, and metric definition. Conflicting measurements are preserved. For scoring, use the median of independent measurements when present; otherwise use the median from the first available tier in this order: community reproduction, vendor reported, derived. Emit a conflict diagnostic whenever more than one candidate record exists.

## Normalization

Normalization occurs within a comparable metric, version, workload, and evaluation setting cohort. Scores are relative to that cohort.

For five or more finite observations, apply the configured transform, then compute `z = (x - median) / (1.4826 × MAD)` and map with `100 × NormalCDF(z)`. Log-skewed lower-is-better metrics use `log1p(x)` before normalization. Lower-is-better scores are inverted after transformation. If MAD is zero, use average-rank percentiles.

For two through four observations, use average-rank percentiles and mark the result provisional. A singleton is unscored. A measured zero-success run is the explicit worst outcome for effective cost/tokens, not missing evidence. Scores are rounded only for presentation.

## Capability

Default domain weights are general reasoning 27.5%, software engineering 27.5%, agentic work 20%, math/science 15%, and context/reliability 10%. Benchmark weights are allocated inside each domain.

Benchmark families are weight budgets. An aggregate and its known constituents share a family budget; adding another representation of the same underlying benchmark cannot increase that family's total influence. Within a family, available benchmark weights are renormalized to the configured family budget. Domain caps prevent excess influence. Empirical correlation is diagnostic only in v1.

## Efficiency

The default metric weights are effective tokens per successful task 50%, turns per task 20%, wall-clock seconds per task 20%, and tool calls per task 10%. `EffectiveTokens = MeanTokensPerAttempt / SuccessRate`. Missing metrics are excluded and remaining weights are renormalized; coverage records the omitted weight.

## Economics

`CostPerSuccessfulTask = MeanCostPerAttempt / SuccessRate`. Headline Economics uses comparable observed cost per successful task only. Advertised input, cached-input, output, cache-write, reasoning-token, long-context, and tool pricing are stored and validated but are not converted into a headline score until workload baskets exist.

## Overall, Value, coverage, and confidence

The default Overall score is `0.55C + 0.25E + 0.20X`. Missing components are renormalized over available component weights; weighted coverage is always reported. Configured sensitivity sets are 55/25/20, 60/20/20, 50/30/20, 60/25/15, and 50/25/25.

Value is separate: `sqrt(Capability × observed-cost-efficiency score)`. It is unavailable without both inputs.

Confidence is High at coverage >=80% and independent/community evidence share >=75%; Medium at coverage >=60% and that evidence share >=50%; otherwise Low. Any small-cohort normalization or failed headline eligibility marks the result provisional.

## Sensitivity, correlation, and Pareto analysis

Sensitivity analysis recomputes scores and reports baseline rank, rank range, score range, maximum rank movement, and stability (`1 - rank_range/(ranked_models-1)`, with one model defined as 1). Correlation output includes Pearson, Spearman, and overlap count; interpretive flags require the configured minimum overlap. Correlation does not alter v1 scores.

A model is Pareto dominated when another model is at least as capable and no more costly/inefficient, with one strict improvement. Equal points do not dominate each other. Outputs name all dominators.

## Unresolved questions

- How should nominal price baskets vary by workload and context length?
- When is overlap sufficient for empirical correlation-based weight reduction?
- How should formal measurement uncertainty and benchmark sampling error propagate?
- How should heterogeneous workload categories combine without hiding user-specific tradeoffs?
- Should evidence tiers receive calibrated quality weights once validation history exists?

