# Enforced source-readiness gate

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

The Artificial Analysis HLE v4.1 adapter consumes a facts-only reviewed extract. It preserves the
published source rate in `evaluation_settings`, converts that rate to configured percentage points,
and uses the access date only as `measurement_as_of_date`. The exact fallback-qualified Fable row
is rejected by crosswalk before measurement construction.
