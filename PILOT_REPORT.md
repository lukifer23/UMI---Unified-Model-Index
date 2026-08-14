# UMI v0.3 multi-source pilot report

## Publication decision

**Real evidence, provisional partial ranking. No headline UMI score or publishable rank.**

The five configurations remain visible, but none passes the inherited v0.2.1 coverage, component,
workload, and Capability-domain gates. This is the expected outcome, not a failed run.

## Accepted scored evidence

| Configuration | DeepSWE v1.1 pass rate | Arena Agent | Partial Capability | Headline |
|---|---:|---:|---:|---:|
| Claude Opus 5 Max | 74% ± 4 | 0.11998 | 89.33 | null |
| Claude Fable 5 Max | 70% ± 4 | rejected: High only | 50.00 | null |
| GPT-5.6 Sol Max | 73% ± 3 | rejected: xHigh only | 75.00 | null |
| Kimi K3 Max | 69% ± 5 | 0.10538 | 44.85 | null |
| GLM-5.2 Max | 44% ± 2 | 0.06711 | ~0.00 | null |

Partial Capability is cohort-relative and combines only the fixed software-engineering and agentic
family budgets available to each exact configuration. It is not an Overall score. Fable is also
release-window-ineligible because its 2026-06-09 release predates the 2026-06-15 start.

## Diagnostic evidence

- Artificial Analysis Intelligence values are composite references. The Fable value is rejected
  because its label includes an Opus 4.8 fallback deployment.
- Epoch ECI input rows are retained as diagnostic references because their source matrix combines
  heterogeneous harnesses/settings and ECI selects highest results across settings.
- Arena text/style-control ratings are diagnostic preference evidence. Missing or non-Max effort
  labels are rejected.
- DeepSWE cost, token, and step summaries are retained but cannot enter mean-based success adjustment;
  the captured source does not establish arithmetic-mean semantics.

## Why no headline exists

- scored Capability covers only software engineering and agentic work, below the three-domain gate;
- Efficiency coverage is below 0.50 and Economics coverage is below 0.40;
- all potentially useful resource evidence is confined to coding and is statistic-ambiguous;
- missing workload evidence is not reweighted to make the cohort eligible.

The generated [partial ranking](data/pilots/v0.3/processed/partial-ranking.json) has null ranks and
null `headline_overall` for every model. The [source readiness report](data/pilots/v0.3/processed/source-readiness.json),
[overlap report](data/pilots/v0.3/processed/overlap.json), and
[pilot sensitivity report](data/pilots/v0.3/processed/pilot-sensitivity.json) are machine-readable.

## Sensitivity result

Equal-family and source-ablation scenarios are computed without relaxing publication gates. Removing
a source does not redistribute or enlarge its domain budget. Every scenario continues to have a null
headline. These scenarios expose how dependent the partial Capability values are on the pilot's two
scored sources.

## Reproducibility

The pilot build is deterministic and offline. It records exact source revisions, checksums, adapter
versions, accepted records, diagnostics, and rejected rows. The complete audit fingerprint changes
when diagnostic/rejected evidence changes; the scored fingerprint does not.
