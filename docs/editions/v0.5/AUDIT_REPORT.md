# UMI Public v0.5 publication audit

This is the release-governance companion to the governed partial score artifacts. It does not rescore evidence or turn a partial result into a headline.

- edition: `umi-public-v0.5`
- publication scope: `governed_partial`
- headline eligible: `false`
- scored-data fingerprint: `5624c3b417e4c0e42dd35411065f200c38ccfc6b49474f47cb671c2d43a22c6c`

## What is publishable

The v0.5 common-core values are real, deterministic, source-bound scores for exact model configurations. They are published as governed partials. No `headline_overall` value or Overall rank is published; common-core order remains diagnostic and provenance-bound.

## Gate status

| Gate | Observed | Required | Result |
|---|---:|---:|---|
| `capability` | 64.0% | 60.0% | **pass** |
| `efficiency` | 4.5% | 50.0% | **blocked** |
| `economics` | 0.0% | 40.0% | **blocked** |
| `overall` | 5.7% | 60.0% | **blocked** |

## Target-cohort coverage

| Configuration | Governed partial | Capability | Efficiency | Economics | Confidence | Headline |
|---|---:|---:|---:|---:|---|---|
| `claude-fable-5-max` | 54.43 | 8.2% | 4.5% | 0.0% | low | withheld |
| `claude-opus-5-max` | 55.51 | 100.0% | 4.5% | 0.0% | low | withheld |
| `gpt-5.6-sol-max` | 66.27 | 100.0% | 4.5% | 0.0% | low | withheld |
| `kimi-k3-max` | 59.69 | 100.0% | 4.5% | 0.0% | low | withheld |
| `glm-5.2-max` | 54.20 | 86.2% | 4.5% | 0.0% | low | withheld |

## Evidence inventory

Accepted Capability cells: **48 / 75**. Missing cells: **23**. Diagnostic evidence is retained but does not count as scored coverage.

## Blockers

- `candidate-grok-4.5-high`
- `candidate-gemini-3.1-pro-preview`
- `near-miss-gpt-5.6-terra-max`
- `near-miss-gpt-5.6-luna-max`
- `near-miss-claude-sonnet-5-max`
- `near-miss-claude-opus-4-8-max`
- `series-deepswe-mean-cost`
- `construct-context-reliability`
- `construct-language-instruction`
- `construct-interactive-latency`
- `construct-billed-economics`
- `construct-hierarchical-bootstrap`

The complete blocker details remain in `BLOCKER_REPORT.md`. Resolving a blocker requires exact identity, compatible cohort, readiness, rights, and preserved raw artifact evidence; no missing value is imputed.
