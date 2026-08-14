# UMI v0.3 multi-source pilot report

## Publication decision

**Real evidence — model-specific partial estimates. No headline UMI score or universal rank.**

The five configurations remain visible, but none passes the inherited v0.2.1 coverage, component,
workload, and Capability-domain gates. This is the expected outcome, not a failed run.

## Accepted scored evidence

| Configuration | ARC-AGI-2 | DeepSWE v1.1 (95% CI) | GPQA | SciCode | CritPt | Partial Capability | Partial Efficiency | Headline |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Claude Opus 5 Max | 90.42% | 73.65% (69.78–77.52) | 93.88% | 55.67% | 29.14% | 76.96 | 41.67 | null |
| Claude Fable 5 Max | missing | 69.72% (65.69–73.76) | rejected | rejected | rejected | 50.00 | 50.00 | null |
| GPT-5.6 Sol Max | 92.50% | 72.67% (69.84–75.50) | 93.50% | 56.13% | 32.30% | 82.28 | 100.00 | null |
| Kimi K3 Max | 60.42% | 68.51% (63.98–73.05) | 93.12% | 58.68% | 23.40% | 26.84 | 58.33 | null |
| GLM-5.2 Max | rejected: unknown effort | 43.78% (42.05–45.50) | 91.86% | 50.46% | 20.86% | 0.00 | 0.00 | null |

Partial Capability is cohort-relative. Opus, Sol, and Kimi cover 49.375% across ARC-AGI-2 plus the
four earlier task families and three domains. GLM covers 35.625% across four families and two domains;
Fable covers only DeepSWE at 16.5%. Those model-specific partials are not directly rankable across
evidence profiles and are not Overall scores. Fable is also release-window-ineligible because its
2026-06-09 release predates the 2026-06-15 start.

## Diagnostic evidence

- Artificial Analysis Intelligence values are composite references. The Fable value is rejected
  because its label includes an Opus 4.8 fallback deployment.
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

- Opus, Sol, and Kimi reach three Capability domains but only 0.49375 weighted coverage, below 0.60;
  GLM and Fable also remain below the three-domain breadth gate;
- Efficiency coverage is 0.045, below 0.50, and Economics coverage is zero, below 0.40;
- ready resources cover only DeepSWE in one of three configured coding families and three of eight metrics;
- missing workload evidence is not reweighted to make the cohort eligible.

The generated [model-specific partial estimates](data/pilots/v0.3/processed/model-specific-partial-estimates.json)
have no model-specific rank and null `headline_overall` for every model. The five-model
[common-evidence comparison](data/pilots/v0.3/processed/common-evidence-five-model-comparison.json)
uses DeepSWE only because Fable's other benchmark identities are not cleared; the exact three-model
[common-evidence comparison](data/pilots/v0.3/processed/common-evidence-three-model-comparison.json)
uses all four scored series under the current strict identity policy. Both are provisional and separately
labeled. The [source-bound uncertainty report](data/pilots/v0.3/processed/source-bound-uncertainty.json)
re-scores one published bound at a time; it is not probabilistic propagation. The
[source readiness report](data/pilots/v0.3/processed/source-readiness.json),
[overlap report](data/pilots/v0.3/processed/overlap.json), and
[pilot sensitivity report](data/pilots/v0.3/processed/pilot-sensitivity.json) are machine-readable.
The [pilot gap report](data/pilots/v0.3/processed/pilot-gap-report.json) enumerates every configured
benchmark/model cell and every workload-category gate.

## Sensitivity result

Equal-family and source-ablation scenarios are computed without relaxing publication gates. Removing
a source does not redistribute or enlarge its domain budget. Every scenario continues to have a null
headline. These scenarios expose how dependent the four scored benchmark families are on the
pilot's two frozen scored source artifacts.

## Reproducibility

The pilot build is deterministic and offline. It records exact source revisions, checksums, adapter
versions, accepted records, diagnostics, and rejected rows. The complete audit fingerprint changes
when diagnostic/rejected evidence changes; the scored fingerprint does not.
