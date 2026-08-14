# UMI v0.3 multi-source pilot report

## Publication decision

**Real evidence — model-specific partial estimates. No headline UMI score or model-specific rank.**

The five configurations remain visible, but none passes the inherited v0.2.1 coverage, component,
workload, and Capability-domain gates. This is the expected outcome, not a failed run.

## Accepted scored evidence

| Configuration | DeepSWE v1.1 pass rate | Arena Agent | Partial Capability | Headline |
|---|---:|---:|---:|---:|
| Claude Opus 5 Max | 74% ± 4 | diagnostic: no immutable snapshot | 100.00 | null |
| Claude Fable 5 Max | 70% ± 4 | rejected: High only | 50.00 | null |
| GPT-5.6 Sol Max | 73% ± 3 | rejected: xHigh only | 75.00 | null |
| Kimi K3 Max | 69% ± 5 | diagnostic: no immutable snapshot | 25.00 | null |
| GLM-5.2 Max | 44% ± 2 | diagnostic: no immutable snapshot | ~0.00 | null |

Partial Capability is cohort-relative and currently covers DeepSWE's fixed software-engineering
budget only. It is not an Overall score. Fable is also
release-window-ineligible because its 2026-06-09 release predates the 2026-06-15 start.

## Diagnostic evidence

- Artificial Analysis Intelligence values are composite references. The Fable value is rejected
  because its label includes an Opus 4.8 fallback deployment.
- Epoch ECI input rows are retained as diagnostic references because their source matrix combines
  heterogeneous harnesses/settings and ECI selects highest results across settings.
- Arena Agent and text/style-control ratings are diagnostic preference evidence. The Agent artifact
  has exact labels and efforts but no immutable snapshot/deployment identity; missing or non-Max
  effort labels are rejected.
- DeepSWE cost, token, and step summaries are retained but cannot enter mean-based success adjustment;
  the captured source does not establish arithmetic-mean semantics.
- Official token tariffs are now retained for all five configurations, including cached-input rates
  and published cache-write, long-context, and tool-fee terms. They cannot establish cost per task
  until compatible task-level token, tool, and success observations exist.
- Four numeric GPT-5.6 Sol Max release claims are retained as vendor claims. None is silently matched
  to a differently dated or differently harnessed independent result.

## Why no headline exists

- scored Capability covers only software engineering, below the three-domain gate;
- Efficiency coverage is below 0.50 and Economics coverage is below 0.40;
- all potentially useful resource evidence is confined to coding and is statistic-ambiguous;
- missing workload evidence is not reweighted to make the cohort eligible.

The generated [model-specific partial estimates](data/pilots/v0.3/processed/model-specific-partial-estimates.json)
have no model-specific rank and null `headline_overall` for every model. The five-model
[common-evidence comparison](data/pilots/v0.3/processed/common-evidence-five-model-comparison.json)
uses DeepSWE only; the exact three-model
[common-evidence comparison](data/pilots/v0.3/processed/common-evidence-three-model-comparison.json)
also uses DeepSWE only under the current strict identity policy. Both are provisional and separately
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
headline. These scenarios expose how dependent the partial Capability values are on the pilot's two
scored sources.

## Reproducibility

The pilot build is deterministic and offline. It records exact source revisions, checksums, adapter
versions, accepted records, diagnostics, and rejected rows. The complete audit fingerprint changes
when diagnostic/rejected evidence changes; the scored fingerprint does not.
