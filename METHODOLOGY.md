# UMI methodology v0.3

This document is the authority for UMI scoring behavior. Configuration files contain the
current policy values; code must not contradict this document. UMI v0.3 adds a manually reviewed,
multi-source evidence pilot. It does not publish a headline UMI ranking.

## v0.3 source roles and exact identity

The pilot cohort is Claude Opus 5 Max, Claude Fable 5 Max, GPT-5.6 Sol Max, Kimi K3 Max,
and GLM-5.2 Max. It is a union cohort: a source need not cover every configuration, but every
accepted row must have an explicit one-to-one crosswalk proving the source model identifier and
inference effort. Missing effort, fallback configurations, aggregated model labels, and fuzzy name
matches are diagnostic or rejected. Fable 5 remains outside the unchanged release window.

Every signal is classified as composite, preference, task, efficiency, economics, or reference,
and as scored or diagnostic-only. Artificial Analysis Intelligence/Coding/Agentic indices and the
Epoch Capabilities Index are diagnostic composites. Arena text ratings are diagnostic preference
evidence. The exact-match Arena Agent aggregate may score; its constituent signals share its
representation budget and remain diagnostic. Exact Artificial Analysis task results and DeepSWE
v1.1 may score only after the ordinary readiness gate passes.

The directed overlap graph records containment, derivation, duplicate measurements, shared tasks,
shared constructs, and unknown overlap. It must be acyclic. Two scored signals connected by a known
overlap relation must share one explicit budget group; a diagnostic composite has zero scoring
budget. Adding a source never enlarges a domain budget.

Pilot family budgets are hypotheses:

| Domain | Families |
|---|---|
| General reasoning | HLE 1.00 |
| Software engineering | DeepSWE 0.60; Terminal-Bench 2.1 0.25; SciCode 0.15 |
| Agentic work | GDPval-AA v2 0.45; tau3-Banking 0.30; Arena Agent 0.25 |
| Math/science | GPQA Diamond 0.65; CritPt 0.35 |
| Context/reliability | AA-LCR 0.50; AA-Omniscience 0.50 |

Equal-family and source-ablation scenarios test these allocations. They do not relax coverage or
publication gates.

## Aggregation statistics

Source statistics are typed as arithmetic mean, median, total, or unspecified. Only an arithmetic
mean per attempt may enter mean-based success adjustment. Medians, totals, a bare "average", agent
steps, and other semantically unmatched summaries remain visible but do not masquerade as means.
DeepSWE pass rate may contribute Capability. Cost contributes Economics only when its source fact
explicitly establishes arithmetic mean cost per attempted task; the per-success value remains
`mean cost per attempt / success rate`. Token, step, duration, or cost summaries without compatible
mean semantics remain diagnostic.

Because the v0.3 pilot has Efficiency and Economics evidence only for coding work, their weighted
workload coverage cannot reach the existing 0.50 and 0.40 component gates. Partial component and
Overall estimates may be shown, but every `headline_overall` and publishable rank must remain null.
Weights are never redefined merely to manufacture eligibility.

## Scored entity

A UMI configuration is an immutable model snapshot plus inference effort. Where Efficiency or
Economics is measured, it also includes the serving provider, endpoint, and service tier.
Region or hardware is recorded when material. Capability from one deployment is not silently
combined with deployment-dependent cost or latency from another.

The model family is descriptive. The configuration/deployment is the scored entity.

## Record readiness

Every source record has a status: `ready`, `diagnostic_only`, `synthetic`, or `invalid`.

- `ready` real records score only when identity, provenance, compatibility, and artifact fields
  pass the enforced readiness gate in `SOURCE_READINESS.md`.
- `diagnostic_only` records remain loadable and auditable but never influence scores.
- `synthetic` records may score only in conspicuously synthetic fixtures.
- `invalid` records fail structural validation.

Normal scoring filters unready real records. `--allow-unready` is a development-only override.
Any model actually influenced by overridden evidence is provisional, receives Low confidence,
and has both `headline_overall` and publishable rank suppressed.

## Identity and compatibility cohorts

A benchmark comparison series is `(benchmark_id, cohort_key)`. A workload comparison series is
`(workload_category, workload, cohort_key)`. Cohort keys must encode materially relevant harness,
benchmark, prompt, tool, retry, pass@k, effort, and endpoint settings. Labels alone never establish
equivalence.

At most one ready scoring cohort may exist for a benchmark representation or workload identity
without an explicit future merge policy. Additional cohorts must be diagnostic. UMI does not
average local percentiles from disconnected cohorts and does not infer cohort equivalence.

## Consolidation and conflicts

Raw records remain immutable. Within one model and compatible series, UMI selects the first
available provenance tier in this order:

1. independent;
2. community reproduction;
3. vendor reported;
4. derived.

It then takes the median of selected values. Multiple candidates emit a conflict diagnostic and
selected record IDs remain in the result. For success-adjusted metrics, derivation occurs on each
record before tier selection and median consolidation; numerators and success rates from separate
records are never paired.

## Normalization

Normalization is cohort-relative and deterministic.

- At least five observations: apply the configured transform, then robust z-scores using
  `z = (x - median(x)) / (1.4826 * MAD)`, followed by the standard normal CDF mapped to 0–100.
- Two to four observations: use average-rank percentiles and mark contributing models provisional.
- One observation: leave the series unscored.
- Zero MAD: fall back to average-rank percentiles.
- Cost, token, turn, latency, tool-call, and successful-task cost metrics use `log1p` when listed in
  `normalization.yaml`.
- Lower-is-better metrics are inverted after transformation so that every normalized score has
  “higher is better” semantics.

Source NaN and infinity are invalid. Internally derived positive infinity is reserved for measured
zero-success outcomes and normalizes to the explicit worst result. Scores are relative to their
dataset fingerprint and are not timeless absolute measurements.

## Capability

Default domain weights are:

| Domain | Weight |
|---|---:|
| General reasoning | 0.275 |
| Software engineering | 0.275 |
| Agentic work | 0.200 |
| Math/science | 0.150 |
| Context/reliability | 0.100 |

Capability is hierarchical: representations belong to families and families belong to domains.
Aliases with the same `representation_group` share one representation budget. Aggregates and known
constituents must share a family so adding an overlapping label cannot create a new family vote.

For family `f`:

```text
FamilyCoverage_f = sum(available representation weights)
                   / sum(configured representation weights)
```

The family score is the weighted mean over available representation groups. For domain `d`:

```text
DomainScore_d = weighted mean of available FamilyScore_f using family.weight
DomainCoverage_d = sum_f family.weight_f * FamilyCoverage_f
```

Finally:

```text
Capability = weighted mean of available DomainScore_d
CapabilityCoverage = sum_d domain.weight_d * DomainCoverage_d
```

Family weights in each configured domain sum to one. In v0.3, `family.cap` is a configuration
guard: `family.weight <= family.cap`, and domain caps sum to at least one. Scoring uses
`family.weight` directly. A cap does not prevent a family from dominating a partial diagnostic
estimate when other families are missing; hierarchical coverage and headline eligibility expose
that limitation.

## Efficiency

Default metric weights are 50% effective tokens, 20% effective turns, 20% effective wall time,
and 10% effective tool calls. Workload-class weights are configured separately.

For every individual source record `i` and attempt-level resource `x`:

```text
EffectiveResource_i = MeanResourcePerAttempt_i / SuccessRate_i
```

This rule applies to tokens, turns, wall time, and tool calls. At zero success every effective
resource is positive infinity and receives the worst normalized result. UMI therefore measures
resources per successful outcome and never rewards fast failure.

Within a workload class `c`:

```text
MetricCoverage_c = sum(weights of available effective metrics)
EfficiencyCoverage = sum_c WorkloadWeight_c * MetricCoverage_c
```

The partial workload score may reweight across available metrics, but coverage retains every
omitted metric weight. One 10%-weight tool-call observation cannot create full workload coverage.

## Economics

Headline Economics uses comparable observed cost per successful task. Advertised prices and
attempted-task costs are reference-only until a defensible conversion or workload basket exists.

For an attempt-cost source record:

```text
CostPerSuccessfulTask_i = MeanCostPerAttempt_i / SuccessRate_i
```

The ratio is derived per record before consolidation. Zero success is positive infinity and the
worst outcome. Economics is normalized only within one workload/cohort series. Coverage is the sum
of configured workload-class weights with comparable successful-task cost evidence. Costs from
unrelated coding, research, browser, or other workloads are not pooled.

## Overall and headline eligibility

The default partial estimate is:

```text
PartialOverall = 0.55 * Capability + 0.25 * Efficiency + 0.20 * Economics
```

Missing components are reweighted only for `partial_overall_estimate`. The weighted coverage is:

```text
OverallCoverage = 0.55 * CapabilityCoverage
                + 0.25 * EfficiencyCoverage
                + 0.20 * EconomicsCoverage
```

A publishable `headline_overall` requires all of the following:

- all three component scores are present;
- Capability coverage at least 0.60;
- Efficiency coverage at least 0.50;
- Economics coverage at least 0.40;
- weighted Overall coverage at least 0.60;
- Capability evidence in at least three domains;
- weighted Efficiency workload coverage at least 0.50;
- model release date inside the configured release window;
- scoring-ready evidence only.

The inherited v0.2.1 component thresholds are hypotheses, not empirically calibrated constants.
Failure leaves component scores and the partial estimate visible but sets `headline_overall` to
null and suppresses headline rank.

## Value is experimental

Value requires Capability and normalized observed Economics. It is not an established construct.
Configured Overall-weight scenarios are:

```text
balanced_geometric = Capability^0.50 * Economics^0.50
capability_heavy   = Capability^0.70 * Economics^0.30
harmonic           = 2 * Capability * Economics / (Capability + Economics)
```

Scenario names must be unique, the baseline must exist, and mathematically duplicate hypotheses
are rejected. Value output identifies the scenario, formula, and parameters. Value sensitivity
reports score/rank ranges, maximum movement, scenario count, and stability. No Value formula is
declared correct, and publishable Value ranking is limited to headline-eligible configurations.

## Coverage and confidence

Coverage is not an observation count. UMI separately exposes domain, family, representation,
Efficiency metric/workload, Economics workload, evidence-quality, and source-organization breadth.

Confidence is rule-based. Initial High/Medium candidates use configured coverage and
independent-or-community evidence thresholds. These caps then apply:

- failed headline eligibility forces Low Overall confidence;
- unready overridden evidence forces Low and suppresses headlines;
- insufficient Capability breadth forces Low;
- provisional normalization prevents High;
- unresolved selected-evidence conflicts prevent High;
- evidence from one source organization caps confidence at Medium.

Every result includes human-readable reasons. UMI never emits `confidence=high` with a provisional
headline result.

## Sensitivity and analyses

Overall sensitivity recomputes the partial score, weighted coverage, headline eligibility, and
ranking for every weight scenario. Models may enter or exit eligibility. Output reports baseline
eligibility, eligible/ineligible scenario counts, rank and score ranges, movement, and stability.

Correlation treats each `(benchmark_id, cohort_key)` as a separate series, aligns raw directions so
better always points upward, reports Pearson, Spearman, overlap, families, and known overlap, and
withholds interpretation below the configured overlap threshold or for constant series.

Pareto analysis is explicitly scoped by metric, workload category, workload, and cohort key. It
reports dominator IDs. UMI creates no universal cost or efficiency frontier from incomparable tasks.

## Dataset identity

`dataset_fingerprint` hashes canonical serialized complete input data. `scored_data_fingerprint`
hashes the exact readiness-filtered inputs used by scoring; pricing and external reference indexes
are excluded in v0.3. Both include model/deployment identity, raw values, success rates, dates,
cohort and evaluation settings, provenance, configuration fingerprint, and engine/formula/
normalization versions. Records are sorted before SHA-256 hashing and no current timestamp is used.

`cohort_id` is the first 16 hexadecimal characters of `scored_data_fingerprint`. `data_as_of` is the
latest included scoring evaluation date, or the configured release-window end if none exists.
Changing a scored value, success rate, snapshot, cohort, record set, or scoring configuration changes
the scored fingerprint. Adding diagnostic-only evidence changes the complete fingerprint but not the
scored fingerprint.

## Remaining limitations and research questions

- Scores remain cohort-relative; frozen normalization baselines and anchor models are deferred.
- Domain, family, workload, and component weights are policy hypotheses, not empirical estimates.
- No formal uncertainty propagation uses sample sizes or confidence intervals yet.
- No automatic benchmark decorrelation or overlap down-weighting is performed.
- No cross-workload Economics basket has been justified.
- Family-budget calibration, empirical decorrelation, and uncertainty propagation remain research
  questions; v0.3 exposes equal-family and source-ablation results instead of hiding uncertainty.
- Model endpoint drift can still be unknowable when a provider does not publish immutable revisions.
