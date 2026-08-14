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

## Architecture

- `config/` holds all weights, thresholds, benchmark metadata, and normalization rules.
- `data/raw/` is reserved for immutable, sourced real-world YAML records.
- `umi/` contains strict schemas, validation, normalization, component scorers, orchestration, and the CLI.
- `analysis/` contains ranking, sensitivity, correlation, and Pareto utilities.
- `tests/fixtures/` contains conspicuously synthetic data used by tests and examples only.

All derived results include source record identifiers, diagnostics, coverage, confidence, eligibility, and a configuration fingerprint. See [METHODOLOGY.md](METHODOLOGY.md) for scoring policy and [DATA_SCHEMA.md](DATA_SCHEMA.md) for record contracts.

## Limitations

The v1 formulas are explicit hypotheses, not claims of objective truth. Scores are cohort-relative. Small cohorts are provisional. Nominal API pricing is stored but excluded from headline Economics until defensible workload baskets exist. Empirical decorrelation and formal uncertainty intervals remain future work.

