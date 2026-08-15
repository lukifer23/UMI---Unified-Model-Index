# UMI v0.3 multi-source pilot report

## Publication decision

**Real evidence — model-specific partial estimates. No headline UMI score or universal rank.**

The five configurations remain visible, but none passes the inherited v0.2.1 coverage, component,
workload, and Capability-domain gates. This is the expected outcome, not a failed run.

## Scored raw evidence

| Configuration | HLE | AA-LCR | AA-Omniscience | ARC-AGI-2 | DeepSWE v1.1 (95% CI) | CursorBench 3.2 | AA Terminal-Bench 2.1 | GDPval-AA v2 Elo (95% CI) | τ³-Banking | GPQA | SciCode | CritPt | Partial Capability | Partial Efficiency | Headline |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Claude Opus 5 Max | 54.87% | 75.67% | 37.07 | 90.42% | 73.65% (69.78–77.52) | 70.0% | 89.14% | 1848.77 (1826.40–1871.14) | 42.06% | 93.88% | 55.67% | 29.14% | 78.29 | 41.67 | null |
| Claude Fable 5 Max | rejected: fallback | rejected: fallback | rejected: fallback | missing | 69.72% (65.69–73.76) | rejected: fallback unverified | rejected: fallback | rejected: fallback | rejected: fallback | rejected | rejected | rejected | 50.00 | 50.00 | null |
| GPT-5.6 Sol Max | 49.49% | 77.67% | 21.97 | 92.50% | 72.67% (69.84–75.50) | 67.2% | 88.01% | 1725.18 (1708.82–1741.53) | 44.33% | 93.50% | 56.13% | 32.30% | 73.69 | 100.00 | null |
| Kimi K3 Max | 46.90% | 82.67% | 19.70 | 60.42% | 68.51% (63.98–73.05) | 60.8% | 85.02% | 1682.29 (1662.55–1702.04) | 45.98% | 93.12% | 58.68% | 23.40% | 39.48 | 58.33 | null |
| GLM-5.2 Max | 41.15% | 76.67% | 4.43 | rejected: unknown effort | 43.78% (42.05–45.50) | 55.0% | 77.90% | 1506.11 (1491.09–1521.12) | 34.64% | 91.86% | 50.46% | 20.86% | 1.93 | 0.00 | null |

Partial Capability is cohort-relative. Opus, Sol, and Kimi cover 100% across twelve families and
five domains. GLM covers 86.25% across eleven families and five domains; Fable covers only DeepSWE
at 8.25%. Those model-specific partials are not directly rankable across
evidence profiles and are not Overall scores. Fable is also release-window-ineligible because its
2026-06-09 release predates the 2026-06-15 start.

## Stable-panel normalized contributions

The five-model common comparison uses DeepSWE as its single common raw metric. Its secondary
percentile scale is fitted once to Fable, Opus, GLM, Sol, and Kimi, then reused for every display
subset. The three-model Opus/Kimi/GLM comparison uses HLE, DeepSWE, CursorBench, GDPval-AA v2,
Terminal-Bench, τ³-Banking, AA-LCR, AA-Omniscience, GPQA, SciCode, and CritPt; DeepSWE
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

The three-model comparison exhaustively evaluates 512 scenarios from three GDPval-AA source
intervals, three DeepSWE source intervals, and three GPQA standard-error approximations. Opus is
rank 1 centrally, Kimi rank 2, and GLM rank 3. Those ranks remain fixed in all 512 endpoint
scenarios: Opus robustly dominates Kimi and GLM, and Kimi robustly dominates GLM. GPQA intervals are explicitly labeled as
normal approximations using `1.96 × SE`, not source-published confidence intervals.

When a requested group has no ready compatible common series, `umi compare` returns a structured
`insufficient_common_support` abstention with no scores or ranks. Missing support and incompatible
cohorts remain visible; malformed inputs and unknown model IDs still fail.

## Comparison validity and certificate

The retained Opus/Kimi/GLM certificate is `provisional_comparison`, not a headline ranking. All
three configurations share the same eleven canonical benchmark series, evidence-profile ID, eleven
bundle-wide stable normalization panels, and weighted-composite score-scale ID. The certificate
also binds 33 selected benchmark records to nine frozen source-artifact checksums and retains
the 512-scenario rank envelopes. Those bindings—not similar labels—are why its values are directly
comparable. Provisional small-panel normalization and incomplete Capability breadth remain explicit
warnings and prevent the certificate from becoming a universal UMI score.

## Diagnostic evidence

- Artificial Analysis Intelligence values are composite references. The Fable value is rejected
  because its label includes an Opus 4.8 fallback deployment.
- Artificial Analysis HLE v4.1 scores are independent atomic measurements for Opus, Sol, Kimi, and
  GLM on the documented 2,158-question text-only, pass@1 cohort. The facts-only extract retains the
  exact published rates and access date without inventing a run date. Fable is rejected because its
  public HLE label explicitly routes through Opus 4.8 fallback.
- Artificial Analysis GDPval-AA v2 Elo scores are independent task measurements for Opus, Sol,
  Kimi, and GLM on one 220-task public-work-product cohort, with published 95% intervals. Fable is
  rejected because its row explicitly uses Opus 4.8 fallback. Average turns, token summaries, and
  calculated cost components remain diagnostic because Elo is not a binary success denominator and
  the published cost combines provider token counts with live typical cache-hit measurements.
- Artificial Analysis τ³-Banking scores are independent pass@1 measurements for Opus, Sol, Kimi,
  and GLM across 97 tasks repeated five times. Fable is rejected because its row explicitly uses
  Opus fallback. Incomplete operational summaries, calculated rather than billed cost, and
  conflicting public decode-time units remain diagnostic and contribute neither Efficiency nor
  Economics.
- Artificial Analysis AA-LCR scores are independent pass@1 measurements for Opus, Sol, Kimi, and
  GLM across 100 hard long-context questions repeated three times on v4.1.1. Fable is rejected
  because its row explicitly uses fallback. Answer/reasoning token and operational timing/cost
  summaries remain diagnostic because accounting is nonstandard and incomplete and calculated cost
  is not a verified billing ledger.
- Artificial Analysis AA-Omniscience contributes its published reliability Index once for exact
  Opus, Sol, Kimi, and GLM Max rows on 6,000 open-answer questions. Fable's fallback-qualified row
  is rejected. Accuracy, attempt rate, hallucination rate, answer decomposition, token totals,
  calculated costs, and upstream time are reconciled but diagnostic; they do not become extra
  scoring votes or Efficiency/Economics evidence.
- Artificial Analysis Terminal-Bench v2.1 contributes exact pass@1 results for Opus, Sol, Kimi,
  and GLM on 89 tasks repeated three times with Terminus 2 in E2B. Fable's fallback-qualified row
  is rejected. Provider-specific aggregate token counters remain diagnostic and do not become
  cross-provider Efficiency or Economics evidence.
- CursorBench 3.2 solution-correctness scores are independent atomic measurements for Opus, Sol,
  Kimi, and GLM on the current ambiguous multi-file task cohort. Fable is rejected because Cursor
  documents invisible Fable-to-Opus routing and the run does not prove fallback absence. The table's
  cost/task, tokens/task, and steps/task values are retained but excluded from Efficiency and
  Economics without a compatible success denominator and verified deployment identity.
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
  per-record success adjustment. The official 27,558-row ledger reconciles 2,231 scored attempts for
  the five Max configurations and binds every retained mean to its actual observation count. Cached
  tokens, wall duration, and dollar cost remain diagnostic because exact deployment identity is not
  verified; Fable cost is additionally incomplete at 432 observations for 436 scored attempts, and
  the runner derives dollars from LiteLLM pricing rather than a disclosed endpoint-, tier-,
  pricing-revision-, and billing-record-bound task ledger.
- Official token tariffs are now retained for all five configurations, including cached-input rates
  and published cache-write, long-context, and tool-fee terms. They cannot establish cost per task
  until compatible task-level token, tool, and success observations exist.
- Four numeric GPT-5.6 Sol Max release claims are retained as vendor claims. None is silently matched
  to a differently dated or differently harnessed independent result.

## Why no headline exists

- Opus, Sol, Kimi, and GLM now clear the Capability-only 0.60 coverage and three-domain breadth
  gates; Fable remains below both coverage and breadth;
- Efficiency coverage is 0.045, below 0.50, and Economics coverage is zero, below 0.40;
- ready resources cover only DeepSWE in one of three configured coding families and three of eight metrics;
- missing workload evidence is not reweighted to make the cohort eligible.

The generated [model-specific partial estimates](data/pilots/v0.3/processed/model-specific-partial-estimates.json)
have no model-specific rank and null `headline_overall` for every model. The five-model
[common-evidence comparison](data/pilots/v0.3/processed/common-evidence-five-model-comparison.json)
uses DeepSWE only because Fable's other benchmark identities are not cleared; the exact three-model
[common-evidence comparison](data/pilots/v0.3/processed/common-evidence-three-model-comparison.json)
uses all eleven scored series under the current strict identity policy. Both are provisional and separately
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
nine frozen scored source artifacts.

## Reproducibility

The pilot build is deterministic and offline. It records exact source revisions, checksums, adapter
versions, accepted records, diagnostics, and rejected rows. The complete audit fingerprint changes
when diagnostic/rejected evidence changes; the scored fingerprint does not.
