# UMI — Unified Model Index

UMI is a Python-first, auditable framework for comparing specific AI model configurations across capability, efficiency, economics, overall performance, and value. It is designed to answer how much useful capability a user receives for the money and inference effort required—not merely which model tops the most benchmarks.

This initial milestone contains the schemas, configuration, scoring engine, analysis utilities, CLI, and synthetic test data. It intentionally contains **no real model measurements or rankings**.

## Quick start

```powershell
uv sync --extra dev
uv run umi validate --data-dir tests/fixtures
uv run umi rank --data-dir tests/fixtures --format json
uv run umi sensitivity --data-dir tests/fixtures
uv run umi correlations --data-dir tests/fixtures
uv run umi pareto --data-dir tests/fixtures
```

Use `--config-dir config` to select another configuration directory and `--output PATH` to write deterministic JSON or CSV instead of stdout.

| Command | Purpose |
| --- | --- |
| `validate` | Parse strict schemas and report referential, duplication, overlap, eligibility, and provenance diagnostics. |
| `rank` | Calculate Capability, Efficiency, Economics, Overall, Value, coverage, confidence, and ranks. |
| `sensitivity` | Re-rank the cohort under every configured Overall weighting set. |
| `correlations` | Calculate pairwise Pearson, Spearman, and overlap counts for benchmark measurements. |
| `pareto` | Find dominated models for capability versus cost, effective tokens, and latency. |

## Synthetic demonstration

The checked-in fixture produces the following **synthetic-only** Overall results. These values demonstrate tradeoffs and are not claims about real models.

| Rank | Synthetic configuration | Overall | Capability | Efficiency | Economics |
| ---: | --- | ---: | ---: | ---: | ---: |
| 1 | synthetic-beta | 51.55 | 70.67 | 25.79 | 31.18 |
| 2 | synthetic-gamma | 50.00 | 50.00 | 50.00 | 50.00 |
| 3 | synthetic-alpha | 49.87 | 85.28 | 4.63 | 9.06 |
| 4 | synthetic-delta | 45.67 | 26.51 | 64.38 | 75.00 |
| 5 | synthetic-epsilon | 45.60 | 11.77 | 83.57 | 91.16 |

Sensitivity results deliberately show rank movement: for example, synthetic-alpha ranges from rank 1 to rank 5 across the five configured hypotheses. That instability is part of the output, not something UMI hides.

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

The v1 formulas are explicit hypotheses, not claims of objective truth. Scores are cohort-relative. Small cohorts are provisional. Nominal API pricing is stored but excluded from headline Economics until defensible workload baskets exist. Empirical decorrelation and formal uncertainty intervals remain future work.

## Recommended next milestone

Build a source registry and a small, manually reviewed ingestion adapter for one independent evaluator. Populate a narrow cross-model slice, retain the raw capture alongside parsed records, and produce a validation report before broadening coverage. Do not begin with bulk scraping.

