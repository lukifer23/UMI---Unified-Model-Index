# UMI real-data pilot — Artificial Analysis snapshot 2026-07-17

## Decision

**Dataset accepted for methodology learning and reference export. Not accepted for
headline UMI ranking.** This is a six-configuration, single-evaluator measurement
snapshot from a dated Artificial Analysis article, accessed 2026-08-14. Three
checksummed Artificial Analysis model-page fact captures support exact release-date
identity metadata; their mutable performance values are not ingested.

## Cohort and observations

The cohort is Claude Fable 5 max with fallback, GPT-5.6 Sol max, Kimi K3 max,
Grok 4.5 high, GLM-5.2 max, and Muse Spark 1.1 xhigh. The capture contains:

- six Artificial Analysis Intelligence Index reference scores;
- six observed costs per attempted Intelligence Index task;
- four Coding Agent Index measurements;
- three GDPval-AA v2 Elo measurements; and
- three AA-Briefcase Elo measurements.

The source registry points to a checksummed local fact capture. All 22 measurement
records resolve to a model snapshot and the same dated source.

| Configuration | AA Intelligence Index | Cost / attempted task | Coding Agent Index | GDPval-AA v2 Elo | AA-Briefcase Elo |
| --- | ---: | ---: | ---: | ---: | ---: |
| Claude Fable 5 max + fallback | 60 | $2.75 | 77 | 1760 | 1583 |
| GPT-5.6 Sol max | 59 | $1.04 | 80 | 1748 | 1495 |
| Kimi K3 max | 57 | $0.94 | — | 1668 | 1547 |
| Grok 4.5 high | 54 | $0.31 | 76 | — | — |
| GLM-5.2 max | 51 | $0.32 | — | — | — |
| Muse Spark 1.1 xhigh | 51 | $0.26 | 69 | — | — |

## Quality findings

- The dated article is stable enough for a snapshot but is not a raw evaluator
  export. Task counts, uncertainty, endpoint revisions, and harness code versions
  are unavailable.
- Coding Agent Index entries use different named agent harnesses. They are valid as
  comparisons of configured agent systems, not bare-model coding ability.
- AA-Briefcase is private and not independently reproducible.
- All evidence comes from one organization. Confidence therefore remains Low.
- Claude Fable 5's June 9 release predates the configured June 15 eligibility
  window and is retained with a validation warning.
- Artificial Analysis cost is per attempted index task. No source success rate is
  available, so Economics and Value remain unscored.
- The external Intelligence Index spans multiple domains. Assigning it to one UMI
  domain would double count or distort weights, so it remains reference-only.

## Output interpretation

Partial Capability estimates exist for five models and are provisional because
their benchmark cohorts contain only three or four observations. GLM-5.2 has no
domain-specific measurement in the article and remains Capability-unscored. No
model reaches three Capability domains, 60% weighted coverage, or headline
eligibility. `headline_overall` is null for all six models.

The next ingestion should seek a dated evaluator export containing compatible
per-benchmark results for at least three UMI domains, explicit evaluated endpoint
revisions, task counts, and successful-task denominators. Until then, expanding the
model count would add apparent breadth without improving analytical defensibility.
