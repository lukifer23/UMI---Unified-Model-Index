# Enforced source-readiness gate

UMI Public v0.5 is a separate edition. Its scored rows come from the frozen Epoch zip
(`epoch-benchmark-data-2026-08-14`, SHA-256 `35a7c21b…a18b`) and are re-checked by
`umi edition --edition v0.5 audit`. That path does not replace this v0.3 readiness gate.

UMI separates parseability from scoring readiness. `umi validate` reports `schema_valid`,
`scored_inputs_ready`, structural `errors`, `readiness_failures`, and non-blocking `warnings`.
It does not load the source registry by default and exits according to structural validity.
Diagnostic-only records do not make selected scored inputs appear unready.

## Record status

- `ready`: eligible to score only if every applicable check below passes.
- `diagnostic_only`: retained but always excluded from scoring and scored-data fingerprints.
- `synthetic`: permitted only with a synthetic, conspicuously labeled model fixture.
- `invalid`: structural validation error.

## Required for a real scoring record

- known source organization, HTTP(S) URL, and access date;
- evaluator when published;
- exact metric definition;
- benchmark or workload version and harness version;
- typed model identity with assurance at least `label_exact` for Capability;
- exact model, release, and inference-effort labels with fallback/composite behavior ruled out;
- truthful evidence date: evaluation date when established, otherwise measurement-as-of,
  leaderboard publication, or source publication date;
- non-`unspecified` compatibility cohort key;
- structured configuration verification;
- retained inspectable artifact plus `source_artifact_id` and an accurate `capture_type`;
- verified deployment identity for all Economics and endpoint-sensitive Efficiency fields (cached
  tokens, wall time, or dollar cost), including serving provider, endpoint, and service tier when
  those fields define the scored deployment; exact harness-level input/output/reasoning tokens,
  turns, agent steps, and tool calls may score provisionally under the remaining identity gates;
- benchmark/workload identity, direction, unit, and category supplied by typed/configured fields;
- exact successful-attempt count and full-attempt observation counts for every real arithmetic-mean
  Efficiency metric; incomplete means remain diagnostic and cannot share a broader success rate;
- for attempt-ledger evidence, one exact deployment/workload/harness, operational-profile ID,
  interaction profile, versioned success-definition identity, unique attempt IDs, an immutable
  artifact checksum, and raw or archived capture; each metric is aggregated only over its own
  observed rows and partial metrics are split into diagnostics;
- for ready observed Economics, cost on every attempt, at least one successful attempt, exact
  endpoint and service-tier verification, total-cost reconciliation, and provider-billing-record
  evidence; router estimates and pricing replays remain diagnostic;
- no conflicting second ready cohort for the same benchmark representation or workload identity.

Published evaluator, harness owner, run executor, tools, scaffold, retry, context, pass@k, task/trial
counts, standard error, and confidence interval should be preserved when available. UMI never
manufactures missing facts. Artifact access dates and model release dates never stand in for
evaluation/source dates.

## Scoring behavior

Normal scoring admits only ready records and valid synthetic fixtures. Diagnostic and invalid records
never score. Unready real records are filtered before normalization, so unrelated `unspecified`
records cannot form a cohort.

`--allow-unready` exists for development diagnosis. It does not waive publication safeguards: any
affected model is provisional, Low confidence, has `headline_overall: null`, and receives no
publishable rank. Multiple ready cohorts without a merge policy remain a validation error even under
the override.

## Source registry

Source captures live under `data/sources/`. The registry records source URL, access/as-of dates,
artifact path, SHA-256, upstream revision, content type, adapter version, license, attribution, and
redistribution scope. Validation checks path containment, existence, checksum, model evidence
artifact references, record artifact references, and source URL registration. `capture_type`
distinguishes raw payloads, archived snapshots, reviewed extracts, citations, and derived artifacts.

`umi bundle validate` checks only the source, crosswalk, identity, policy, and adapter dependencies
listed in the deterministic acceptance manifest for admitted scoring records. `umi sources validate
--strict` checks the complete registry and audit context. A failure in unused diagnostic evidence
blocks strict archival validity, not governed scoring.

`umi certificate` revalidates that governed bundle and its typed acceptance manifest before
deriving a comparison certificate. A forged or stale manifest fails closed; unrelated diagnostic
artifacts remain outside the certificate's selected-record and checksum bindings.

## Adapter acceptance checklist

Before an adapter is allowed to emit `ready`:

1. freeze or retain an inspectable source artifact;
2. map the exact typed model identity and deployment facts without fuzzy joins or invented snapshots;
3. define benchmark/workload and compatibility cohort deterministically;
4. preserve raw numeric values and published sample metadata;
5. assign provenance tier, capture type, and structured configuration verification honestly;
6. prove that diagnostic rows are excluded and multiple cohorts fail safely;
7. add adversarial fixtures for missing identity, non-finite values, and version collisions;
8. run validation, tests, Ruff, mypy, and CLI smoke tests.

The v0.3 crosswalk must prove exact model, release, effort, and relevant deployment identity.
Missing effort, mismatched effort, fallback/composite aliases, collisions, and revision mismatches
reject the row. A valid diagnostic row remains auditable but cannot score.

Acquisition is separate from ingestion. Adapters consume frozen local artifacts only; runtime HTTP,
scraping, and credentials are prohibited in the scoring path.

The DeepSWE public trial ledger independently reconciles all 2,231 selected scored attempts for the
five Max configurations. It also proves that Fable cost is observed for only 432 of 436 scored
attempts. UMI retains the per-metric counts, but cached tokens, wall time, and cost remain diagnostic
without complete deployment identity; the incomplete Fable cost mean cannot score under any status
flip.

The Artificial Analysis HLE v4.1 adapter consumes a facts-only reviewed extract. It preserves the
published source rate in `evaluation_settings`, converts that rate to configured percentage points,
and uses the access date only as `measurement_as_of_date`. The exact fallback-qualified Fable row
is rejected by crosswalk before measurement construction.

The Artificial Analysis GDPval-AA v2 adapter consumes a facts-only access-date snapshot because
the public Bradley-Terry reference parameters may change with the comparison pool. Exact Opus, Sol,
Kimi, and GLM Max rows are ready for Capability with their 95% sandwich-estimator intervals. The
fallback-qualified Fable row is rejected. Average turns, output-token summaries, and calculated
cost components remain diagnostic settings: Elo is not a binary success denominator, and the
published cost combines provider token counts with live typical cache-hit measurements rather than
an endpoint- and billing-revision-bound task ledger.

The Artificial Analysis τ³-Banking adapter consumes a facts-only access-date snapshot of the
97-task, five-repeat public cohort. Exact Opus, Sol, Kimi, and GLM Max rows are ready for Capability;
the fallback-qualified Fable row is rejected. The adapter preserves the tau2-bench v1.0.1 harness,
BM25-plus-grep retrieval, backend-state grading, 200-step ceiling, task/trial counts, and source
rates. Token and calculated-cost fields are incomplete across the cohort, and the public page gives
conflicting units for weighted decode time. Those operational fields therefore remain diagnostic
and cannot enter Efficiency or Economics.

The Artificial Analysis AA-LCR adapter consumes a facts-only access-date snapshot of the v4.1.1
100-question, three-repeat public cohort. Exact Opus, Sol, Kimi, and GLM Max rows are ready for
Capability; the fallback-qualified Fable row is rejected. The adapter preserves the published
pass@1 rates, task/trial counts, context scale, category count, document scale, grader, and equality
checker. Answer/reasoning tokens and operational timing/cost fields remain diagnostic because
provider accounting is nonstandard, coverage is incomplete, and calculated cost is not a verified
deployment- and billing-revision-bound task ledger.

The Artificial Analysis AA-Omniscience adapter consumes a facts-only access-date snapshot of the
v4.1.1 6,000-question, 42-topic, single-pass cohort. Exact Opus, Sol, Kimi, and GLM Max rows are
ready for Capability; the fallback-qualified Fable row is rejected. The adapter independently
reconciles the published Index against correct and incorrect counts, all answer classes against the
task total, derived accuracy/attempt/hallucination rates, output-token components, and calculated
cost components. Only the source-defined Omniscience Index scores. Operational aggregates remain
diagnostic without exact endpoint, tier, billing revision, and attempt-ledger identity.

The Artificial Analysis Terminal-Bench v2.1 adapter consumes a facts-only access-date snapshot of
the common 89-task, three-repeat cohort run with Terminus 2 in an E2B sandbox. Exact Opus, Sol,
Kimi, and GLM Max rows are ready for Capability; the fallback-qualified Fable row is rejected. The
adapter preserves the source rates, 267-attempt count, pass@1 semantics, 250-episode ceiling,
timeout policy, and aggregate provider token counters. The token counters remain diagnostic because
provider tokenization differs, cacheable input is not an observed cache-hit or billing ledger, and
attempt-level resource rows are absent.

The CursorBench 3.2 adapter consumes a facts-only reviewed extract from the official leaderboard.
Exact Opus, Sol, Kimi, and GLM Max labels are ready for Capability. The Fable row is rejected because
the public run does not rule out Cursor's documented invisible Fable-to-Opus routing. Cost/task,
tokens/task, and steps/task remain retained diagnostic settings, not Efficiency or Economics inputs:
the score is not documented as a binary success rate suitable for success adjustment, and endpoint
plus service-tier identity is not verified.
