# UMI — Unified Model Index

UMI is an auditable Python library and CLI for scoring model configurations across Capability,
Efficiency, Economics, Overall, and experimental Value. Version 0.2.1 stabilizes scoring and
data-readiness invariants before a multi-source real-data pilot.

There is currently no publishable real UMI ranking. The checked-in synthetic fixtures demonstrate
the engine; the narrow Artificial Analysis capture remains a provenance pilot, not a unified score.

## Install and verify

Python 3.11 or newer and [uv](https://docs.astral.sh/uv/) are required.

```bash
uv sync --extra dev
uv run pytest
uv run ruff check .
uv run mypy
```

The lockfile is committed. Use `uv sync --frozen` when reproducing an existing lock.

## CLI

Run the complete synthetic pipeline:

```bash
uv run umi validate --data-dir tests/fixtures --config-dir tests/fixtures/config
uv run umi rank --data-dir tests/fixtures --config-dir tests/fixtures/config --format json
uv run umi sensitivity --data-dir tests/fixtures --config-dir tests/fixtures/config
uv run umi value-sensitivity --data-dir tests/fixtures --config-dir tests/fixtures/config
uv run umi correlations --data-dir tests/fixtures --config-dir tests/fixtures/config
uv run umi pareto --data-dir tests/fixtures --config-dir tests/fixtures/config
```

`validate` reports `schema_valid` and `scoring_ready` separately. `rank` publishes only eligible
headlines by default; `--include-provisional` shows partial results without turning them into
headlines. `--allow-unready` is development-only: affected results remain provisional, Low
confidence, and unranked.

JSON and CSV output are deterministic. Every result contains component scores, hierarchical
coverage, confidence reasons, provenance record IDs, configuration and dataset fingerprints,
cohort identity, and engine/formula/normalization versions.

## Python API

```python
from umi import load_dataset, load_project_config, score_dataset

dataset = load_dataset("tests/fixtures")
config = load_project_config("tests/fixtures/config")
results = score_dataset(dataset, config)

for result in results:
    print(result.model_id, result.headline_overall, result.confidence)
```

Analysis APIs are in `analysis`: ranking, Overall sensitivity, Value sensitivity, correlation, and
workload/cohort-specific Pareto frontiers.

## Scoring at a glance

The default partial Overall formula is:

```text
0.55 * Capability + 0.25 * Efficiency + 0.20 * Economics
```

Missing evidence may produce `partial_overall_estimate`, but a headline requires all three component
scores, component-specific minimum coverage, at least 60% weighted Overall coverage, Capability in
three domains, sufficient Efficiency workload coverage, an eligible release date, and scoring-ready
evidence.

Attempt-level tokens, turns, wall time, tool calls, and cost are divided by the same record's success
rate before provenance selection and median consolidation. Zero success is an explicit worst outcome,
not missing data. Capability and coverage aggregate hierarchically across representations, families,
and domains.

The complete specification is [METHODOLOGY.md](METHODOLOGY.md). Do not infer scoring behavior from a
README summary.

## Repository layout

```text
analysis/             sensitivity, correlations, rankings, Pareto tools
config/               default scoring policy
data/raw/             narrow manually captured provenance pilot
data/sources/         source registry and checksummed captures
schemas/              generated machine-readable JSON Schemas
scripts/              deterministic schema generator
tests/fixtures/        conspicuously synthetic scoring data
umi/                   typed schemas, validation, readiness, scoring, CLI
METHODOLOGY.md         authoritative formulas and policy
DATA_SCHEMA.md         explanatory schema guide
SOURCE_READINESS.md    enforced ingestion gate
AGENTS.md              repository safeguards
```

## Architecture

Loading preserves frozen source records. Validation checks structural integrity separately from
scoring readiness. The readiness layer filters records before every scorer. Capability, Efficiency,
and Economics normalize only compatible cohorts, return selected provenance, and calculate
hierarchical coverage. The scoring layer applies headline and confidence rules and fingerprints the
complete and scored datasets. Analysis tools reuse readiness and compatibility rules.

Pydantic generates `schemas/dataset.schema.json`, `schemas/config.schema.json`, and
`schemas/scoring-result.schema.json`. Regenerate them after model changes:

```bash
uv run python scripts/generate_schemas.py
```

## Current limitations

- UMI scores are cohort-relative and change when the scored cohort changes.
- Weights and eligibility thresholds are transparent hypotheses, not empirical calibration.
- Sample sizes and intervals are preserved but not propagated through scoring.
- No fixed reference cohort, anchor scale, decorrelation weighting, or cross-workload cost basket
  exists yet.
- External composites such as Epoch ECI and preference leaderboards such as Arena cannot be added as
  unrestricted benchmark votes; their overlap and construct roles must be specified first.
- The current real capture uses one evaluator and lacks Efficiency/successful-task Economics breadth,
  so it cannot produce a headline UMI score.

## Next milestone

After v0.2.1 is accepted, the next task is a four-to-six-configuration, manually reviewed source
crosswalk—not a broad scrape. It should inventory exact overlap among Artificial Analysis, Epoch ECI
or its underlying benchmark data, Arena, and selected task-level benchmarks; assign each source a
scoring/reference role; freeze source snapshots; and ingest only exact configuration/cohort matches.
