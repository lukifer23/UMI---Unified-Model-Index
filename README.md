# UMI — Unified Model Index

UMI is a Python-first, auditable framework for comparing specific AI model configurations across capability, efficiency, economics, overall performance, and value. It is designed to answer how much useful capability a user receives for the money and inference effort required—not merely which model tops the most benchmarks.

This initial milestone contains the schemas, configuration, scoring engine, analysis utilities, CLI, and synthetic test data. It intentionally contains **no real model measurements or rankings**.

## Quick start

```powershell
uv sync --extra dev
uv run umi validate --data-dir tests/fixtures
uv run umi rank --data-dir tests/fixtures --format json
uv run umi sensitivity --data-dir tests/fixtures
uv run umi value-sensitivity --data-dir tests/fixtures
uv run umi correlations --data-dir tests/fixtures
uv run umi pareto --data-dir tests/fixtures
```

Use `--config-dir config` to select another configuration directory and `--output PATH` to write deterministic JSON or CSV instead of stdout.

| Command | Purpose |
| --- | --- |
| `validate` | Parse strict schemas and report referential, duplication, overlap, eligibility, and provenance diagnostics. |
| `rank` | Calculate Capability, Efficiency, Economics, Overall, Value, coverage, confidence, and ranks. |
| `sensitivity` | Re-rank the cohort under every configured Overall weighting set. |
| `value-sensitivity` | Test experimental Value formulas and report rank ranges. |
| `correlations` | Calculate pairwise Pearson, Spearman, and overlap counts for benchmark measurements. |
| `pareto` | Find dominated models for capability versus cost, effective tokens, and latency. |

## Synthetic demonstration

The checked-in fixture produces the following **synthetic-only** Overall results. These values demonstrate tradeoffs and are not claims about real models.

| Rank | Synthetic configuration | Overall | Capability | Efficiency | Economics |
| ---: | --- | ---: | ---: | ---: | ---: |
| 1 | synthetic-alpha | 65.5 | 85.3 | 40.9 | 41.8 |
| 2 | synthetic-beta | 59.4 | 70.7 | 45.2 | 46.2 |
| 3 | synthetic-gamma | 50.0 | 50.0 | 50.0 | 50.0 |
| 4 | synthetic-delta | 38.8 | 26.5 | 52.9 | 55.0 |
| 5 | synthetic-epsilon | 32.3 | 11.8 | 56.7 | 58.2 |

These figures are rounded presentation values; machine output retains full
precision. Sensitivity and Value-sensitivity outputs expose rank movement when a
fixture or future cohort is unstable rather than hiding it.

## Architecture

- `config/` holds all weights, thresholds, benchmark metadata, and normalization rules.
- `data/raw/` is reserved for immutable, sourced real-world YAML records.
- `umi/` contains strict schemas, validation, normalization, component scorers, orchestration, and the CLI.
- `analysis/` contains ranking, sensitivity, correlation, and Pareto utilities.
- `tests/fixtures/` contains conspicuously synthetic data used by tests and examples only.

```text
.
├── analysis/       ranking, sensitivity, correlation, and Pareto utilities
├── config/         benchmark, weight, normalization, and eligibility policy
├── data/           empty real-data inputs plus source-note storage
├── tests/          behavioral tests and synthetic-only fixtures
├── umi/            schemas, validation, scoring components, orchestration, CLI
├── AGENTS.md       guardrails for future coding agents
├── DATA_SCHEMA.md  input and output contracts
└── METHODOLOGY.md  authoritative scoring decisions
```

All derived results include source record identifiers, diagnostics, coverage, confidence, eligibility, and a configuration fingerprint. See [METHODOLOGY.md](METHODOLOGY.md) for scoring policy and [DATA_SCHEMA.md](DATA_SCHEMA.md) for record contracts.

## Limitations

The serialized API distinguishes diagnostic `partial_overall_estimate` from
nullable publishable `headline_overall`; it never emits an ambiguous `overall`.
Results include workload/family/source coverage, confidence reasons, experimental
Value methodology, and the exact scoring cohort. Value is not an established fact.

The v1 formulas are explicit hypotheses, not claims of objective truth. Scores are cohort-relative. Small cohorts are provisional. Nominal API pricing is stored but excluded from headline Economics until defensible workload baskets exist. Empirical decorrelation and formal uncertainty intervals remain future work.

## Recommended next milestone

Build a source registry and a small, manually reviewed ingestion adapter for one independent evaluator. Populate a narrow cross-model slice, retain the raw capture alongside parsed records, and produce a validation report before broadening coverage. Do not begin with bulk scraping.
