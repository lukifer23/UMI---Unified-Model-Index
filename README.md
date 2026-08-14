# UMI — Unified Model Index

UMI is an auditable Python library and CLI for comparing exact model configurations across
Capability, Efficiency, Economics, Overall, and experimental Value. Version 0.3.1 adds a real,
five-configuration, multi-source evidence pilot. It does **not** publish a headline UMI score:
the evidence supports provisional partial Capability estimates only.

The pilot cohort is Claude Opus 5 Max, Claude Fable 5 Max, GPT-5.6 Sol Max, Kimi K3 Max, and
GLM-5.2 Max. Its frozen sources are Artificial Analysis public facts, Epoch ECI, LM Arena Agent and
text/style-control rows, and DeepSWE v1.1 facts. Every source row is accepted only through an exact
model-and-effort crosswalk.

## Install and verify

Python 3.11 or newer and [uv](https://docs.astral.sh/uv/) are required.

```bash
uv sync --frozen --extra dev --no-editable
PYTHONPATH=. uv run --no-sync pytest
PYTHONPATH=. uv run --no-sync ruff check .
PYTHONPATH=. uv run --no-sync mypy
```

`--no-editable` makes the installed CLI testable on Python 3.14, whose site loader ignores
Hatchling's underscore-prefixed editable `.pth` file. The explicit `PYTHONPATH=.` makes the
quality checks measure the checked-out source; run the install and CLI smoke commands below as
the package-level verification.

## Reproduce the v0.3 pilot

All adapters are pure and offline. Acquisition is separate; the committed build reads only frozen
artifacts.

`scripts/freeze_v03_open_sources.py --accept-network` is the explicit acquisition path for Epoch and
Arena. It is never called by ingestion or scoring. AA and DeepSWE remain reviewed-fact inputs.

```bash
uv run --no-sync python scripts/build_v03_pilot.py
uv run --no-sync umi sources validate --data-dir data/pilots/v0.3/raw
uv run --no-sync umi crosswalk
uv run --no-sync umi overlap
uv run --no-sync umi ingest --source aa
uv run --no-sync umi ingest --source epoch
uv run --no-sync umi ingest --source arena-agent
uv run --no-sync umi ingest --source arena-text
uv run --no-sync umi ingest --source deepswe
uv run --no-sync umi estimates --data-dir data/pilots/v0.3/raw
uv run --no-sync umi compare --data-dir data/pilots/v0.3/raw --models claude-fable-5-max claude-opus-5-max glm-5.2-max gpt-5.6-sol-max kimi-k3-max
uv run --no-sync umi compare --data-dir data/pilots/v0.3/raw --models claude-opus-5-max kimi-k3-max glm-5.2-max
uv run --no-sync umi uncertainty --data-dir data/pilots/v0.3/raw
uv run --no-sync umi pilot-sensitivity --data-dir data/pilots/v0.3/raw
uv run --no-sync umi correlations --data-dir data/pilots/v0.3/raw
uv run --no-sync umi pareto --data-dir data/pilots/v0.3/raw
```

Every model-specific output is labeled `real evidence — model-specific partial estimate`; it is
not a ranking. All `headline_overall` fields are null. `umi compare` produces a separately labeled,
provisional rank only after explicitly restricting the requested models to their common evidence.

The synthetic engine demonstration remains available under `tests/fixtures` and is always labeled
as synthetic.

## Architecture

```text
frozen artifacts -> offline adapters -> exact crosswalk -> readiness filter
                 -> overlap/family budgets -> compatible-cohort normalization
                 -> component estimates -> eligibility/publication gates
```

- `METHODOLOGY.md` is authoritative for formulas and policy.
- `data/sources/registry.yaml` records checksums, revisions, licenses, attribution, and redistribution.
- `data/sources/v0.3/crosswalk.yaml` records every exact match and reviewed rejection.
- `config/overlap.yaml` assigns signal roles and directed overlap relationships.
- `data/pilots/v0.3/raw/` contains generated typed inputs; `processed/` contains deterministic reports.
- `umi/adapters/` contains source-specific, no-network transformations.
- `schemas/` contains generated JSON Schemas for data, config, source, crosswalk, overlap, and output.

Complete and scored-data fingerprints are deliberately different. Rejected and diagnostic evidence,
crosswalk decisions, and artifact checksums affect the complete fingerprint. The scored fingerprint
contains only accepted scoring records plus the scored-artifact audit manifest, adapter versions, and
governed scoring configuration. The overlap policy is included through the configuration fingerprint.

## Scoring summary

The default Overall formula remains:

```text
0.55 × Capability + 0.25 × Efficiency + 0.20 × Economics
```

Capability retains the five domain weights and v0.3 fixes within-domain benchmark-family budgets.
DeepSWE pass rate contributes to software engineering. Arena Agent rows retain exact source labels,
effort, construct, and source-declared intervals, but are diagnostic: the frozen artifact does not
identify an immutable model snapshot or deployment. AA composites, ECI rows, Arena text ratings, and
DeepSWE resource summaries are diagnostic only.

DeepSWE's published “Avg cost”, output tokens, and steps are not treated as arithmetic means because
the captured source does not establish that statistic. They therefore cannot be divided by success
rate or enter Efficiency/Economics. This prevents a convenient but unsupported headline.

## Current limitations

- Only two Capability domains have scored evidence; three are required for headline eligibility.
- Efficiency and Economics evidence is coding-only and, in this capture, not mean-qualified.
- Fable 5 Max predates the unchanged 2026-06-15 release-window start.
- Scores are cohort-relative; no fixed anchor cohort or formal uncertainty propagation exists.
- Family budgets are documented pilot hypotheses, not empirical decorrelation weights.
- Arena text/style-control is a bounded diagnostic snapshot, not a complete historical extract.
- No frontend, database, scraper, credentials, or live network path is part of the scoring library.

See [PILOT_REPORT.md](PILOT_REPORT.md), [SOURCE_READINESS.md](SOURCE_READINESS.md), and
[SOURCES_AND_LICENSES.md](SOURCES_AND_LICENSES.md) for the audit trail and publication decision.

## Recommended next ingestion task

Freeze exact, task-level public facts for HLE, GPQA Diamond/CritPt, and one context/reliability family
for the same five configurations, including evaluation dates, harness versions, task counts, and
configuration evidence. In parallel, obtain an explicitly arithmetic-mean, attempt-level resource
export covering at least three configured workload categories. Do not broaden the cohort or relax a
gate to manufacture a headline.
