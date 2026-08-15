# UMI v0.3 multi-source pilot report

## Publication decision

**Real evidence — model-specific partial estimates. No headline UMI score or universal rank.**

The five configurations remain visible, but none passes the inherited v0.2.1 coverage, component,
workload, and Capability-domain gates. This is the expected outcome, not a failed run.

## Scored raw evidence

| Configuration | HLE | ARC-AGI-2 | DeepSWE v1.1 (95% CI) | GPQA | SciCode | CritPt | Partial Capability | Partial Efficiency | Headline |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Claude Opus 5 Max | 54.87% | 90.42% | 73.65% (69.78–77.52) | 93.88% | 55.67% | 29.14% | 81.98 | 41.67 | null |
| Claude Fable 5 Max | rejected: fallback | missing | 69.72% (65.69–73.76) | rejected | rejected | rejected | 50.00 | 50.00 | null |
| GPT-5.6 Sol Max | 49.49% | 92.50% | 72.67% (69.84–75.50) | 93.50% | 56.13% | 32.30% | 78.88 | 100.00 | null |
| Kimi K3 Max | 46.90% | 60.42% | 68.51% (63.98–73.05) | 93.12% | 58.68% | 23.40% | 28.25 | 58.33 | null |
| GLM-5.2 Max | 41.15% | rejected: unknown effort | 43.78% (42.05–45.50) | 91.86% | 50.46% | 20.86% | 0.00 | 0.00 | null |

Partial Capability is cohort-relative. Opus, Sol, and Kimi cover 63.125% across six families and
three domains. GLM covers 49.375% across five families and three domains; Fable covers only DeepSWE
at 16.5%. Those model-specific partials are not directly rankable across
evidence profiles and are not Overall scores. Fable is also release-window-ineligible because its
2026-06-09 release predates the 2026-06-15 start.

## Stable-panel normalized contributions

The five-model common comparison uses DeepSWE as its single common raw metric. Its secondary
percentile scale is fitted once to Fable, Opus, GLM, Sol, and Kimi, then reused for every display
subset. The three-model Opus/Kimi/GLM comparison uses HLE, DeepSWE, GPQA, SciCode, and CritPt; DeepSWE
still uses the five-model panel and GPQA still uses its four accepted models. For example, Kimi's
DeepSWE stable-panel percentile remains 25 whether Sol is displayed or omitted.

Every processed comparison exposes the panel members and IDs, requested `robust_z` strategy,
applied small-cohort percentile fallback, raw contributions, absolute configured weights, composite
score, evidence-profile ID, and score-scale ID. These percentile positions are relative ranks on a
declared panel, not capability-distance measurements.

## Rank sensitivity

The five-model DeepSWE comparison exhaustively evaluates 32 joint endpoint scenarios from five
source-declared intervals. Its central order is Opus, Sol, Fable, Kimi, GLM. The first four can each
occupy ranks 1–4 under the endpoint scenarios, while GLM remains rank 5; each of the first four
robustly dominates GLM. The result does not claim probabilities.

The three-model comparison exhaustively evaluates 64 scenarios from three DeepSWE source intervals
and three GPQA standard-error approximations. Opus and Kimi can each occupy rank 1 or 2. GLM remains
rank 3, while Opus and Kimi each robustly dominate it. GPQA intervals are explicitly labeled as
normal approximations using `1.96 × SE`, not source-published confidence intervals.

When a requested group has no ready compatible common series, `umi compare` returns a structured
`insufficient_common_support` abstention with no scores or ranks. Missing support and incompatible
cohorts remain visible; malformed inputs and unknown model IDs still fail.

## Comparison validity and certificate

The retained Opus/Kimi/GLM certificate is `provisional_comparison`, not a headline ranking. All
three configurations share the same five canonical benchmark series, evidence-profile ID, five
bundle-wide stable normalization panels, and weighted-composite score-scale ID. The certificate
also binds fifteen selected benchmark records to three frozen source-artifact checksums and retains
the 64-scenario rank envelopes. Those bindings—not similar labels—are why its values are directly
comparable. Provisional small-panel normalization and incomplete Capability breadth remain explicit
warnings and prevent the certificate from becoming a universal UMI score.

## Diagnostic evidence

- Artificial Analysis Intelligence values are composite references. The Fable value is rejected
  because its label includes an Opus 4.8 fallback deployment.
- Artificial Analysis HLE v4.1 scores are independent atomic measurements for Opus, Sol, Kimi, and
  GLM on the documented 2,158-question text-only, pass@1 cohort. The facts-only extract retains the
  exact published rates and access date without inventing a run date. Fable is rejected because its
  public HLE label explicitly routes through Opus 4.8 fallback.
- Epoch ECI input rows are retained as diagnostic references because their source matrix combines
  heterogeneous harnesses/settings and ECI selects highest results across settings.
- Epoch's raw GPQA archive supplies four scoring-ready exact Max rows. Fable is rejected because the
  CSV does not prove fallback routing was absent and the linked run log was access-controlled.
- The same frozen Epoch archive supplies creator-run SciCode and CritPt results for four exact Max
  configurations. Their execution dates are not established, so UMI keeps `evaluation_date` null
  and uses the frozen measurement-as-of date for freshness. Fable's rows explicitly include Opus
  4.8 fallback and are rejected.
- ARC Prize verified-leaderboard ARC-AGI-2 rows score for Opus, Sol, and Kimi on the semi-private
  120-task pass@2 cohort. One duplicate Opus source ID whose display label says High is rejected,
  as is GLM's unknown-effort row. Published task cost is retained as metadata, not Economics.
- Arena Agent and text/style-control ratings are diagnostic preference evidence. The Agent artifact
  has exact labels and efforts but no immutable snapshot/deployment identity; missing or non-Max
  effort labels are rejected.
- DeepSWE arithmetic-mean input/output tokens and agent steps enter provisional Efficiency after
  per-record success adjustment. Wall duration and dollar cost remain diagnostic because exact
  deployment identity is not verified.
- Official token tariffs are now retained for all five configurations, including cached-input rates
  and published cache-write, long-context, and tool-fee terms. They cannot establish cost per task
  until compatible task-level token, tool, and success observations exist.
- Four numeric GPT-5.6 Sol Max release claims are retained as vendor claims. None is silently matched
  to a differently dated or differently harnessed independent result.

## Why no headline exists

- Opus, Sol, and Kimi now clear the Capability-only 0.60 coverage and three-domain breadth gates;
  GLM remains below Capability coverage at 0.49375, and Fable remains below both coverage and breadth;
- Efficiency coverage is 0.045, below 0.50, and Economics coverage is zero, below 0.40;
- ready resources cover only DeepSWE in one of three configured coding families and three of eight metrics;
- missing workload evidence is not reweighted to make the cohort eligible.

The generated [model-specific partial estimates](data/pilots/v0.3/processed/model-specific-partial-estimates.json)
have no model-specific rank and null `headline_overall` for every model. The five-model
[common-evidence comparison](data/pilots/v0.3/processed/common-evidence-five-model-comparison.json)
uses DeepSWE only because Fable's other benchmark identities are not cleared; the exact three-model
[common-evidence comparison](data/pilots/v0.3/processed/common-evidence-three-model-comparison.json)
uses all five scored series under the current strict identity policy. Both are provisional and separately
labeled, lead with raw values, and carry stable-panel and score-scale identity. The
[three-model comparison certificate](data/pilots/v0.3/processed/comparison-certificate-three-model.json)
adds the governed bundle, source-record, artifact-checksum, identity, and deterministic result
fingerprint proof. The
[source-bound uncertainty report](data/pilots/v0.3/processed/source-bound-uncertainty.json)
re-scores one published bound at a time; it is not probabilistic propagation. The
[source readiness report](data/pilots/v0.3/processed/source-readiness.json),
[overlap report](data/pilots/v0.3/processed/overlap.json), and
[pilot sensitivity report](data/pilots/v0.3/processed/pilot-sensitivity.json) are machine-readable.
The [pilot gap report](data/pilots/v0.3/processed/pilot-gap-report.json) enumerates every configured
benchmark/model cell and every workload-category gate.

## Sensitivity result

Equal-family and source-ablation scenarios are computed without relaxing publication gates. Removing
a source does not redistribute or enlarge its domain budget. Every scenario continues to have a null
headline. These scenarios expose how dependent the scored benchmark families are on the pilot's
three frozen scored source artifacts.

## Reproducibility

The pilot build is deterministic and offline. It records exact source revisions, checksums, adapter
versions, accepted records, diagnostics, and rejected rows. The complete audit fingerprint changes
when diagnostic/rejected evidence changes; the scored fingerprint does not.
