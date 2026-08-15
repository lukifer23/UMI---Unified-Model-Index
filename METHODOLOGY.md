# UMI methodology v0.3.4

This document is the authority for UMI scoring behavior. Configuration files contain the
current policy values; code must not contradict this document. UMI v0.3.4 retains the manually reviewed,
multi-source evidence pilot. It does not publish a headline UMI ranking.

## v0.3 source roles and exact identity

The pilot cohort is Claude Opus 5 Max, Claude Fable 5 Max, GPT-5.6 Sol Max, Kimi K3 Max,
and GLM-5.2 Max. It is a union cohort: a source need not cover every configuration, but every
accepted row must have an explicit one-to-one crosswalk proving the source model identifier and
inference effort. Missing effort, fallback configurations, aggregated model labels, and fuzzy name
matches are diagnostic or rejected. Fable 5 remains outside the unchanged release window.

Every signal is classified as composite, preference, task, efficiency, economics, or reference,
and as scored or diagnostic-only. Artificial Analysis Intelligence/Coding/Agentic indices and the
Epoch Capabilities Index are diagnostic composites. Arena text ratings and Arena Agent are
diagnostic preference evidence. The frozen Arena Agent artifact provides exact model labels and
effort, but not an immutable provider snapshot or deployment identifier. The aggregate is excluded
because it is diagnostic preference evidence, not because named-release identity is categorically
insufficient for Capability. Its constituent signals share its representation budget and remain
diagnostic. Exact task results may score only after the ordinary readiness gate passes.

The directed overlap graph records containment, derivation, duplicate measurements, shared tasks,
shared constructs, and unknown overlap. It must be acyclic. Two scored signals connected by a known
overlap relation must share one explicit budget group; a diagnostic composite has zero scoring
budget. Adding a source never enlarges a domain budget.

Pilot family budgets are hypotheses:

| Domain | Families |
|---|---|
| General reasoning | HLE 0.50; ARC-AGI-2 0.50 |
| Software engineering | DeepSWE 0.60; Terminal-Bench 2.1 0.25; SciCode 0.15 |
| Agentic work | GDPval-AA v2 0.60; tau3-Banking 0.40; Arena Agent diagnostic 0.00 |
| Math/science | GPQA Diamond 0.65; CritPt 0.35 |
| Context/reliability | AA-LCR 0.50; AA-Omniscience 0.50 |

Equal-family and source-ablation scenarios test these allocations. They do not relax coverage or
publication gates.

`BenchmarkFamilyDefinition.cap` is retained only for schema compatibility in v0.3 and is
deprecated. UMI does not dynamically redistribute family weights through caps; removal is deferred
to a later schema-breaking release.

ARC-AGI-2 and HLE split the General-reasoning domain equally as a transparent pilot hypothesis:
ARC-AGI-2 measures few-shot fluid abstraction and exact grid transformation, while HLE measures
broad expert-level question answering. Neither may stand in for the other. The split is fixed before
ARC scores enter normalization, and missing HLE remains missing coverage rather than being
reweighted into ARC-AGI-2. ARC records use the verified semi-private 120-task leaderboard, pass@2,
one published run, direct input-to-output prediction, and no client-side tools. Unknown effort and
source/display-label conflicts are rejected.

Arena Agent's aggregate is a causal/field-utility preference construct rather than an atomic task
success measurement. v0.3.1 therefore follows the constituent-first policy: the aggregate remains
diagnostic with zero Capability weight, while future compatible constituent task signals may enter
their own documented budgets. The former positive Arena allocation is redistributed between the
two active agentic task families in their prior 0.45:0.30 ratio. Diagnostic Arena evidence cannot
increase coverage, confidence, or source diversity.

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

A UMI configuration is an explicitly typed model identity plus inference effort. It may be a named
release, versioned endpoint, immutable provider snapshot, or immutable open-weight revision; UMI
does not upgrade one kind into another. Where Efficiency or Economics is measured, it also includes
the serving provider, endpoint, and service tier.
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

## Release claims and calibration (v0.3.1 evidence contract)

A lab release claim is a first-class, immutable diagnostic record. It records the literal claim,
the exact configuration, benchmark representation, raw value, unit, direction, compatibility
cohort, evaluation date, and the claim's retained source artifact. Claims are not benchmark
measurements and never score merely because they resemble one.

UMI may compare a claim only with a ready, independent or community-reproduction benchmark
measurement that matches all of: canonical configuration, compatible typed identity, benchmark
representation, unit, direction, and compatibility cohort. A comparison reports the signed and
absolute difference and preserves both record IDs. Missing compatible evidence, a different
cohort, an incompatible identity, a different unit or direction, a non-independent observation, or
an unready observation is an explicit non-comparison, not a zero difference or an inferred match.

Claim-calibration reports are descriptive. They may show compatibility coverage and error for the
specific claims represented in a frozen dataset; they do not assign a universal truthfulness score
to a lab, normalize claims into benchmark results, or alter UMI weights, confidence, readiness, or
headline eligibility. Any future use of vendor-reported atomic measurements remains subject to the
ordinary provenance-tier and readiness rules and must be ingested as a separately typed
measurement with an explicit overlap decision.

The retired `raw_artifact_available` boolean is not canonical provenance: artifact existence and
quality are represented by `source_artifact_id`, the source registry, checksum validation, and
`capture_type`. The offline loader discards this legacy key when reading older frozen artifacts;
it does not rewrite those artifacts or infer a capture type from the boolean.

Official token tariffs are also frozen as descriptive evidence. A pricing record may preserve
uncached input, cached input, five-minute cache-write, one-hour cache-write, output, long-context
multiplier, and per-tool fees when the source publishes them. A missing tariff field is unknown,
not zero. Model-level tariffs do not establish task Economics: UMI requires compatible observed
per-attempt resource use and success before deriving cost per successful task. Tariffs and release
claims change the complete audit fingerprint but not the scored fingerprint unless a future,
documented scoring rule explicitly consumes them.

Descriptive model notes and diagnostic `evidence_artifact_ids` are excluded from the scored
fingerprint and retained in the complete audit fingerprint. Otherwise adding a citation to an
unchanged scored configuration would falsely create a new scoring cohort.

## Identity and compatibility cohorts

A benchmark comparison series is `(benchmark_id, cohort_key)`. A workload comparison series is
`(workload_category, workload_family, workload, cohort_key)`. Cohort keys must encode materially relevant harness,
benchmark, prompt, tool, retry, pass@k, effort, and endpoint settings. Labels alone never establish
equivalence.

One model may not have multiple ready scoring cohorts for the same benchmark representation or
workload identity without an explicit future selection policy. Different models may retain ready
evidence from different cohorts, but those records form separate series: UMI does not merge them,
infer cohort equivalence, or compare them as common support. A comparison spanning only such
incompatible cohorts abstains and identifies the conflict.

## Governed scoring bundle

Real-data scoring requires a validated bundle containing the typed dataset, scoring configuration,
source registry, exact model crosswalk, overlap policy, and typed acceptance manifest. The manifest
deterministically lists accepted record, artifact, crosswalk, and signal IDs; excluded diagnostic
and unready records; scoring-relevant adapter versions; warnings; and a content fingerprint.
`score_bundle()` revalidates both the governed inputs and this manifest, so a caller cannot bypass
the factory and silently alter the admitted evidence. Every scored record
binds its `signal_id`, `crosswalk_entry_id`, and `source_registry_snapshot_id`. Before scoring, UMI
verifies the artifact checksum and revision, exact canonical model and effort mapping, signal role
and disposition, and the benchmark's signal-to-budget allocation. Every scored record also declares
whether its evidence capture is a raw upstream payload, archived source snapshot, reviewed fact
extract, citation-only reference, or derived artifact. Capture type is provenance, not proof of
reproducibility. Synthetic fixtures use a separate test path. Optional side-command validation is
not a substitute for this bundle.

Validation has three deliberately separate scopes. `umi validate` checks typed structure,
references, cohorts, and configuration consistency without loading a source registry by default;
its exit status reflects structural validity, while `scored_inputs_ready` separately reports
whether selected scored records pass readiness. `umi bundle validate` is the scoring trust boundary
and checks only accepted scoring records and the artifacts, exact crosswalk entries, identities,
signals, budgets, and adapter versions they depend on. `umi sources validate --strict` checks the
complete archival package, including diagnostic evidence, pricing, release claims, rejected
crosswalk context, licensing, attribution, and every registered artifact. Therefore a broken
diagnostic artifact fails strict audit validity but cannot invalidate a score that does not consume
it. Headline eligibility remains a model-result property and is never inferred from schema or audit
validity.

Benchmark definitions bind one overlap-policy signal and budget group. A budget group resolves to
one `(domain, family, representation_group)` allocation; mappings across domains or families are
invalid. Record-level `scoring_disposition` cannot override a diagnostic policy.

## Model identity truthfulness

UMI scores the canonical configuration ID, not a marketing family and not an assumed provider
checkpoint. Every model declares an `identity_kind` and `identity_assurance`. The pilot configurations
are exact named releases at Max effort with `label_exact` assurance; none is represented as an
immutable provider snapshot. `evidence_artifact_ids` are source captures, not model snapshots.

Capability records may score provisionally when the named release, release label, and effort label
are exact, fallback/composite behavior is ruled out, the source date is known, and identity
assurance is at least `label_exact`. Efficiency observations of wall time, cached tokens, or dollar
cost and all Economics observations additionally require verified deployment identity because
endpoint, serving provider, service tier, caching, and infrastructure can materially change those
measurements. Exact harness-level input/output/reasoning-token counts, turns, agent steps, and tool
calls may score provisionally without endpoint identity when the source proves the exact named
release, effort, fallback state, harness, cohort, and arithmetic-mean semantics. Endpoint-sensitive
fields must be isolated in a separate record so they cannot make a compatible harness-resource
record appear deployable. A `provider_snapshot_id` may be populated only when the provider actually
publishes an immutable identifier.

Date fields are not interchangeable. `evaluation_date` is populated only when the source establishes
the execution date. Otherwise freshness/readiness uses the first available truthful source date in
this order: measurement-as-of date, leaderboard publication date, then source publication date.
Artifact access date and model release date do not become evaluation dates. Outputs expose the
latest contributing evidence date under this rule as `data_as_of`.

For the frozen Artificial Analysis results redistributed in Epoch's Benchmarking Hub archive,
`harness_version` names the accessed public AA methodology profile, not an undisclosed code revision.
SciCode uses the documented 288 test subproblems over three repeats with scientist-background
prompting; CritPt uses the documented 70 test challenges over five repeats and official grader. The
archive does not expose execution dates, so these records retain null `evaluation_date`, a truthful
measurement-as-of date, and `reproducible: false`.

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

Component computations distinguish selected scoring evidence, excluded candidates, diagnostic
evidence, and conflicting selected evidence. Only selected scoring evidence may affect scores,
profiles, source diversity, confidence, source record IDs, or scored-input fingerprints. In
particular, attempted-task and non-mean cost records remain visible as excluded Economics evidence
without entering Economics confidence or provenance.

## Normalization

Normalization is cohort-relative and deterministic. Production comparisons use a stable panel for
each `(benchmark_id, cohort_key, canonical_representation_group)` series. That panel contains every
ready, compatible normalization member in the accepted scored bundle; filtering the displayed
models never refits it. A local-subset percentile is not a production mode.

Each representation group has exactly one configured priority-zero canonical representation.
Aliases use a larger explicit `selection_priority`. For one model and cohort, UMI uses the available
representation with the lowest configured priority, so adding a later-sorting or earlier-sorting
alias cannot displace canonical evidence. Common support and panel identity use the canonical group,
while selected alias record IDs remain visible in provenance.

- At least eight observations: apply the configured transform, then robust z-scores using
  `z = (x - median(x)) / (1.4826 * MAD)`, followed by the standard normal CDF mapped to 0–100.
- Two to seven observations: use average-rank percentiles and mark contributing models provisional.
- One observation: leave the series unscored.
- Zero MAD: fall back to average-rank percentiles.
- Cost, token, turn, latency, tool-call, and successful-task cost metrics use `log1p` when listed in
  `normalization.yaml`.
- Lower-is-better metrics are inverted after transformation so that every normalized score has
  “higher is better” semantics.

Every applied normalization exposes its requested strategy, actual strategy, panel size, thresholds,
fallback reason, transform, direction inversion, and provisional flag. A stable-panel score is a
relative position, not a raw capability distance. Comparisons therefore lead with raw benchmark
values and expose normalized values, configured absolute weights, weighted contributions, panel
IDs, evidence-profile IDs, and one score-scale ID. Normalized composite scores are directly
comparable only when evidence profile, score scale, formula version, normalization version, and
configuration fingerprint all match.

The baseline robust-z threshold is eight observations. Five-model pilot series therefore use
average-rank percentiles, are explicitly marked small-cohort, and cannot be presented as precise
interval-scale differences. Robust-z and capped-robust-z remain sensitivity methods to be reported
separately; neither changes headline eligibility.

## Typed uncertainty

Uncertainty is source-declared metadata, not a fabricated error model. A measurement may retain a
typed confidence interval with its known confidence level, a published plus-or-minus margin whose
confidence level is unknown, or a standard error. Bounds, units, source-field labels, and missing
confidence levels are preserved explicitly. A published margin is not upgraded to a 95% confidence
interval, and a source interval with no stated level retains `confidence_level: null`.

UMI may calculate deterministic bounded sensitivity only when a source supplies usable numeric
bounds. It must label the result as source-bound sensitivity, preserve the central estimate, and
never treat bound endpoints as independent observations. No confidence interval is synthesized from
sample count, and uncertainty alone cannot change readiness, coverage, weights, or eligibility.

Source NaN and infinity are invalid. Internally derived positive infinity is reserved for measured
zero-success outcomes and normalizes to the explicit worst result. Scores are relative to their
dataset fingerprint and are not timeless absolute measurements.

For an explicit comparison group, UMI performs deterministic joint rank sensitivity when at most
12 contributing records have usable uncertainty. Source bounds are used literally; published
margins become `value ± margin`; a published standard error becomes a clearly labeled
`value ± 1.96 × SE` normal-approximation interval. Percent metrics are clamped to 0–100. UMI
enumerates every lower/upper corner, recomputes the whole common-evidence comparison on the same
stable panel membership, and reports score and possible-rank envelopes plus strict robust dominance.
Scenario counts are not probabilities, and UMI does not report probability-best or pairwise win
probability.

When requested models have no ready compatible common series, comparison is a successful structured
abstention rather than an exception. It reports missing support by model, incompatible series, and
recommended missing evidence. Unknown model IDs, malformed bundles, and invalid policy remain
errors.

Model-specific partial estimates never receive ordinal ranks. The removed
`rank --include-provisional` path cannot promote them; only explicit common-evidence comparisons or
future headline-eligible Overall results may rank models.

Default correlation output is fail-closed. Below the configured overlap threshold, for a constant
series, for incompatible cohorts, or for known-overlap pairs, Pearson and Spearman values are null
and `interpretability_reason` explains why.

Pareto analysis requires one shared Capability evidence-profile ID and score-scale ID across all
participating models. Otherwise it returns a structured abstention. Full common-support Pareto
recomputation is deferred until real operational expense evidence exists.

Sensitivity deltas expose baseline and scenario support, scale, coverage, and raw scores. A score
change is comparable only when both evidence profile and score scale remain unchanged. No-op
equal-family cases are explicitly non-informative.

## Comparison certificate

The UMI Comparison Certificate is a deterministic rendering of one governed common-evidence
comparison, not a second scoring implementation. It binds the requested configuration IDs to the
validated acceptance manifest, scored-input fingerprint, common evidence profile, stable
normalization panels, score scale, raw and normalized contributions, identity assurance, selected
record IDs, source artifacts and checksums, and joint rank-sensitivity envelope. Its result
fingerprint is SHA-256 over the canonical JSON contents excluding `result_fingerprint` itself.

A certificate is `provisional_comparison` while any contributing comparison score is provisional.
If no common ready series exists, it is `insufficient_common_support` and retains the comparison
engine's missing-support and incompatibility diagnostics; it never manufactures a profile, scale,
score, or rank. `valid_comparison` is reserved for a future comparison that clears all provisional
conditions. Bundle validation errors remain command errors rather than signed-looking certificates.

Fingerprint roles are deliberately distinct: `complete_audit_fingerprint` covers all retained
scored and diagnostic context; `scored_input_fingerprint` covers the exact readiness-filtered
scoring context and governed scoring configuration; and certificate `result_fingerprint` covers
the exact comparison group and emitted result. The acceptance-manifest fingerprint is exposed as
`bundle_fingerprint`; it is not a synonym for any of these three content scopes.

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

### v0.3.1 partial-evidence weighting and comparability

For a scoring representation group `r`, UMI computes one flattened configured budget:

```text
AbsoluteWeight_r = DomainWeight_r × FamilyWeight_r
                   × RepresentationWeight_r / SumFamilyRepresentationWeights_r
```

For a partial Capability estimate, UMI uses only available representation groups in both the
numerator and denominator:

```text
PartialCapability = sum(AbsoluteWeight_r × NormalizedScore_r) / sum(AbsoluteWeight_r)
CapabilityCoverage = sum(AbsoluteWeight_r)
```

It does not renormalize an available family to a full domain budget before combining domains.
DeepSWE retains its configured absolute budget of `0.275 × 0.60 = 0.165`; missing Terminal-Bench or
SciCode lowers coverage and does not make DeepSWE a full software-engineering vote. Arena Agent had
a `0.20 × 0.25 = 0.05` budget in the earlier experimental policy, but the v0.3.1 construct decision
makes that aggregate diagnostic with zero weight. It therefore cannot enter this formula.

Aliases in one `representation_group` use a deterministic canonical representation. Additional
aliases do not increase coverage or budget, and they cannot alter a score merely by being added.

Every component result exposes an evidence profile. Its `id` hashes its methodological support
series and configuration; its `evidence_record_fingerprint` separately hashes the exact selected
records. Two partial estimates are directly comparable only when they share formula and
normalization versions, configuration fingerprint, and evidence-profile ID. Model-specific partial
estimates are never a shared ranking. A common-evidence comparison first intersects the ready
benchmark series `(benchmark_id, cohort_key)` available to every requested configuration, then
recomputes each score using only that intersection.

Efficiency and Economics use the same rule with workload support rather than benchmark support.
Their profile records every normalized workload/category/cohort/metric series. They are comparable
only when those workload-series sets and the scoring configuration match; a cost result cannot be
ranked beside a different task, cohort, or resource definition.

Family weights in each configured domain sum to one. In v0.3, `family.cap` is a configuration
guard: `family.weight <= family.cap`, and domain caps sum to at least one. Scoring uses
`family.weight` directly. A cap does not prevent a family from dominating a partial diagnostic
estimate when other families are missing; hierarchical coverage and headline eligibility expose
that limitation.

## Efficiency

The v0.3.4 pilot metric hypothesis is 15% effective input tokens, 15% effective output tokens,
10% effective reasoning tokens, 10% effective cached tokens, 10% effective turns, 15% effective
agent steps, 15% effective wall time, and 10% effective tool calls. These are policy weights, not
empirically learned parameters. Token subtypes are kept distinct: a total-token field is not scored
alongside its constituent input/output fields.

Workload coverage uses a fixed configured hierarchy:

```text
component -> workload category -> workload family -> workload series -> metric
```

Within the pilot coding category, family weights are 40% software-repository agents, 30%
terminal-environment agents, and 30% code-repair agents. DeepSWE v1.1 is the sole currently
configured software-repository workload; Terminal-Bench 2.1 and CursorBench are the initial named
workloads for the other two families. These are explicit pilot hypotheses and will receive
sensitivity analysis before a headline release. Categories without an approved family profile have
zero available coverage and cannot be represented by an arbitrary observed workload.

For every individual source record `i` and attempt-level resource `x`:

```text
EffectiveResource_i = MeanResourcePerAttempt_i / SuccessRate_i
```

This rule applies independently to input, output, reasoning, and cached tokens, turns, agent steps,
wall time, and tool calls. At zero success every effective
resource is positive infinity and receives the worst normalized result. UMI therefore measures
resources per successful outcome and never rewards fast failure.

Within category `c`, family `f`, workload `w`, and metric `m`:

```text
WorkloadMetricScore_wm = normalize comparable cohort values
FamilyMetricScore_fm = weighted_available_w(WorkloadMetricScore_wm, WorkloadWeight_w)
CategoryMetricScore_cm = weighted_available_f(FamilyMetricScore_fm, FamilyWeight_f)
CategoryScore_c = weighted_available_m(CategoryMetricScore_cm, MetricWeight_m)
EfficiencyScore = weighted_available_c(CategoryScore_c, CategoryWeight_c)

EfficiencyCoverage = sum_c CategoryWeight_c
                       * sum_f FamilyWeight_f
                       * sum_w WorkloadWeight_w
                       * sum_m available_wm * MetricWeight_m
```

Each partial aggregation may reweight only across available children at that exact hierarchy level;
coverage retains every omitted category, family, workload, and metric weight. One workload cannot
stand in for an entire category, and one low-weight observation cannot create full workload coverage.

## Economics

Headline Economics uses comparable observed cost per successful task. Advertised prices and
attempted-task costs are reference-only until a defensible conversion or workload basket exists.

For an attempt-cost source record:

```text
CostPerSuccessfulTask_i = MeanCostPerAttempt_i / SuccessRate_i
```

The ratio is derived per record before consolidation. Zero success is positive infinity and the
worst outcome. Economics is normalized only within one workload/cohort series and aggregated through
the same fixed category/family/workload hierarchy. Coverage retains missing family and workload
weights. Costs from unrelated coding, research, browser, or other workloads are not pooled.

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

`dataset_fingerprint` hashes canonical serialized complete audit input data. `scored_data_fingerprint`
hashes a separate, explicit scoring context: the exact readiness-filtered benchmark, efficiency, and
task-economics records; scored model configurations; the governed scoring-configuration fingerprint;
scored-artifact audit manifest; adapter versions; and engine/formula/normalization versions. Pricing,
external references, complete-audit metadata, and diagnostic-only records are excluded in v0.3.
Model configurations with no readiness-filtered scoring record are excluded as evidence-free.
Records are sorted before SHA-256 hashing and no current timestamp is used.

`cohort_id` is the first 16 hexadecimal characters of `scored_data_fingerprint`. `data_as_of` is the
latest included scoring evaluation date, or the configured release-window end if none exists.
Changing a scored value, success rate, typed identity, cohort, record set, or scoring configuration changes
the scored fingerprint. Adding diagnostic-only evidence changes the complete fingerprint but not the
scored fingerprint.

## Remaining limitations and research questions

- Scores remain cohort-relative; frozen normalization baselines and anchor models are deferred.
- Domain, family, workload, and component weights are policy hypotheses, not empirical estimates.
- Typed source-declared uncertainty is preserved, but no broad probabilistic propagation across
  heterogeneous benchmark constructs is justified yet.
- No automatic benchmark decorrelation or overlap down-weighting is performed.
- No cross-workload Economics basket has been justified.
- Family-budget calibration, empirical decorrelation, and uncertainty propagation remain research
  questions; v0.3 exposes equal-family and source-ablation results instead of hiding uncertainty.
- Model endpoint drift can still be unknowable when a provider does not publish immutable revisions.
