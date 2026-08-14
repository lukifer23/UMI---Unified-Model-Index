# Enforced source-readiness gate

UMI separates parseability from scoring readiness. `umi validate` reports `schema_valid`,
`scoring_ready`, structural `errors`, `readiness_failures`, and non-blocking `warnings`.

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
- immutable model snapshot matching the scored configuration;
- evaluation date;
- non-`unspecified` compatibility cohort key;
- explicit configuration verification;
- retained raw/inspectable artifact plus `source_artifact_id`;
- serving provider, endpoint, and service-tier match when those fields define the scored deployment;
- benchmark/workload identity, direction, unit, and category supplied by typed/configured fields;
- no conflicting second ready cohort for the same benchmark representation or workload identity.

Published evaluator, harness owner, run executor, tools, scaffold, retry, context, pass@k, task/trial
counts, standard error, and confidence interval should be preserved when available. UMI never
manufactures missing facts.

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
artifact path, and SHA-256. Validation checks path containment, existence, checksum, model snapshot
references, record artifact references, and source URL registration. A boolean
`raw_artifact_available` without an artifact reference is not enough for real scoring readiness.

## Adapter acceptance checklist

Before an adapter is allowed to emit `ready`:

1. freeze or retain an inspectable source artifact;
2. map exact model snapshot and deployment identity without fuzzy joins;
3. define benchmark/workload and compatibility cohort deterministically;
4. preserve raw numeric values and published sample metadata;
5. assign provenance tier and configuration verification honestly;
6. prove that diagnostic rows are excluded and multiple cohorts fail safely;
7. add adversarial fixtures for missing identity, non-finite values, and version collisions;
8. run validation, tests, Ruff, mypy, and CLI smoke tests.
