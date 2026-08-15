# UMI — Unified Model Index

UMI is an auditable Python library and CLI for comparing exact model configurations across
Capability, Efficiency, Economics, Overall, and experimental Value. Version 0.3.10 extends the real,
five-configuration, multi-source pilot with exact AA-Omniscience, AA-LCR, τ³-Banking, GDPval-AA v2, HLE, CursorBench 3.2, DeepSWE,
GPQA Diamond, SciCode, CritPt, and ARC-AGI-2 results plus DeepSWE confidence intervals and
harness-resource means. It does **not**
publish a headline UMI score: the evidence supports only provisional, model-specific partial
Capability and Efficiency estimates.

The pilot cohort is Claude Opus 5 Max, Claude Fable 5 Max, GPT-5.6 Sol Max, Kimi K3 Max, and
GLM-5.2 Max. Its frozen sources are Artificial Analysis public facts, Epoch ECI and Benchmarking Hub
data, AA-Omniscience, AA-LCR, τ³-Banking, GDPval-AA v2, and CursorBench 3.2 facts, LM Arena Agent and text/style-control rows, and
DeepSWE v1.1 facts. Every source row is accepted only through an exact model-and-effort crosswalk.

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

`uv run --no-sync python scripts/freeze_v03_open_sources.py --accept-network --snapshot-id ID` is the explicit,
non-overwriting acquisition path for Epoch ECI, the complete Benchmarking Hub archive, and Arena.
It writes a checksum manifest to a fresh
snapshot directory and is never called by ingestion or scoring. Arena acquisition freezes the
revision-addressed raw Parquet files; promotion into adapter input is a separate reviewed step.
AA, CursorBench, DeepSWE, and lab releases remain reviewed-fact inputs.

```bash
uv run --no-sync python -m scripts.build_v03_pilot
PYTHONPATH=. uv run --no-sync umi validate --data-dir tests/fixtures --config-dir tests/fixtures/config
PYTHONPATH=. uv run --no-sync umi bundle validate --data-dir data/pilots/v0.3/raw
PYTHONPATH=. uv run --no-sync umi sources validate --strict --data-dir data/pilots/v0.3/raw
PYTHONPATH=. uv run --no-sync umi crosswalk
PYTHONPATH=. uv run --no-sync umi overlap
PYTHONPATH=. uv run --no-sync umi ingest --source aa
PYTHONPATH=. uv run --no-sync umi ingest --source aa-hle
PYTHONPATH=. uv run --no-sync umi ingest --source aa-gdpval
PYTHONPATH=. uv run --no-sync umi ingest --source aa-lcr
PYTHONPATH=. uv run --no-sync umi ingest --source aa-omniscience
PYTHONPATH=. uv run --no-sync umi ingest --source aa-tau3
PYTHONPATH=. uv run --no-sync umi ingest --source cursorbench
PYTHONPATH=. uv run --no-sync umi ingest --source epoch
PYTHONPATH=. uv run --no-sync umi ingest --source epoch-benchmarks
PYTHONPATH=. uv run --no-sync umi ingest --source arena-agent
PYTHONPATH=. uv run --no-sync umi ingest --source arena-text
PYTHONPATH=. uv run --no-sync umi ingest --source deepswe
PYTHONPATH=. uv run --no-sync umi ingest --source lab-anthropic
PYTHONPATH=. uv run --no-sync umi ingest --source lab-openai
PYTHONPATH=. uv run --no-sync umi ingest --source lab-kimi
PYTHONPATH=. uv run --no-sync umi ingest --source lab-zai
PYTHONPATH=. uv run --no-sync umi estimates --data-dir data/pilots/v0.3/raw
PYTHONPATH=. uv run --no-sync umi compare --data-dir data/pilots/v0.3/raw --models claude-fable-5-max claude-opus-5-max glm-5.2-max gpt-5.6-sol-max kimi-k3-max
PYTHONPATH=. uv run --no-sync umi compare --data-dir data/pilots/v0.3/raw --models claude-opus-5-max kimi-k3-max glm-5.2-max
PYTHONPATH=. uv run --no-sync umi certificate --data-dir data/pilots/v0.3/raw --models claude-opus-5-max kimi-k3-max glm-5.2-max
PYTHONPATH=. uv run --no-sync umi uncertainty --data-dir data/pilots/v0.3/raw
PYTHONPATH=. uv run --no-sync umi pilot-sensitivity --data-dir data/pilots/v0.3/raw
PYTHONPATH=. uv run --no-sync umi correlations --data-dir data/pilots/v0.3/raw
PYTHONPATH=. uv run --no-sync umi pareto --data-dir data/pilots/v0.3/raw
PYTHONPATH=. uv run --no-sync umi claims --data-dir data/pilots/v0.3/raw
PYTHONPATH=. uv run --no-sync umi gaps --data-dir data/pilots/v0.3/raw
```

The build also regenerates `data/pilots/v0.3/processed/pilot-dashboard.json`, the canonical
source-backed contract for the five-model interactive report. It has partial status and is not a
second scoring implementation or a headline ranking.
`data/pilots/v0.3/processed/pilot-dashboard.html` is the committed self-contained rendering; its
embedded manifest, snapshot, and sources are tested against the canonical JSON after every build.

Every model-specific output is labeled `real evidence — model-specific partial estimate`; it is
not a ranking. All `headline_overall` fields are null. `umi compare` produces a separately labeled,
provisional rank only after explicitly restricting the requested models to their common evidence.
It leads with raw benchmark values and uses bundle-wide stable normalization panels: hiding a model
from the display never refits another model's percentile. Every normalized contribution includes
its applied fallback trace, absolute configured weight, panel ID, and score-scale ID. Joint
lower/upper sensitivity reports possible-rank and robust-dominance envelopes, never probabilities.
Requests with no compatible common evidence return a structured abstention and exit successfully.

`umi certificate` converts that governed comparison into one deterministic, source-bound JSON
proof. It answers why the values are comparable by binding the requested configurations to the
acceptance manifest, scored-input fingerprint, common evidence profile, stable panels, score scale,
raw and normalized contributions, rank envelope, exact selected records, artifacts, and checksums.
It emits the same structured abstention when the comparison has no common ready support.

The synthetic engine demonstration remains available under `tests/fixtures` and is always labeled
as synthetic.

All real-data analysis commands construct the governed scoring bundle first. Its deterministic,
typed acceptance manifest records exactly which scored records, artifacts, crosswalk entries,
signals, and adapter versions are admitted, and `score_bundle()` revalidates it. A checksum mismatch,
non-exact crosswalk, unknown or diagnostic signal, revision mismatch, or signal/budget mismatch
in accepted evidence fails before scoring. Unrelated diagnostic evidence is checked by
`umi sources validate --strict` and cannot block a score it does not feed. The direct
`score_dataset` function is the isolated synthetic-fixture path; production CLI flows use
`ScoringBundle`.

## Architecture

```text
frozen artifacts -> offline adapters -> governed scoring bundle -> readiness filter
                 -> overlap/family budgets -> compatible-cohort normalization
                 -> component estimates -> eligibility/publication gates
```

- `METHODOLOGY.md` is authoritative for formulas and policy.
- `data/sources/registry.yaml` records checksums, revisions, licenses, attribution, and redistribution.
- `data/sources/v0.3/crosswalk.yaml` records every exact match and reviewed rejection.
- `config/overlap.yaml` assigns signal roles and directed overlap relationships.
- `data/pilots/v0.3/raw/` contains generated typed inputs; `processed/` contains deterministic reports.
- `umi/adapters/` contains source-specific, no-network transformations.
- `schemas/` contains generated JSON Schemas for data, config, source, crosswalk, overlap,
  acceptance manifest, normalization panels, score scales, benchmark contributions, typed common
  comparisons, and output.

Complete and scored-data fingerprints are deliberately different. Rejected and diagnostic evidence,
crosswalk decisions, and artifact checksums affect the complete fingerprint. The scored fingerprint
contains only accepted scoring records plus the scored-artifact audit manifest, adapter versions, and
governed scoring configuration. The overlap policy is included through the configuration fingerprint.
Each benchmark representation group has one explicit priority-zero canonical definition; aliases
use larger configured priorities and cannot displace canonical evidence through lexical ordering.

## Scoring summary

The default Overall formula remains:

```text
0.55 × Capability + 0.25 × Efficiency + 0.20 × Economics
```

Capability retains the five domain weights and fixed within-domain benchmark-family budgets.
HLE and ARC-AGI-2 contribute to general reasoning; CursorBench, DeepSWE, and SciCode contribute to software engineering;
GPQA Diamond and CritPt contribute to math/science. The frozen Epoch archive supplies exact Max rows
for Opus, Sol, Kimi, and GLM on the AA benchmarks, and exact ARC rows for Opus, Sol, and Kimi. Fable's
archive rows remain rejected because SciCode and CritPt identify an Opus 4.8 fallback composite and
GPQA does not establish fallback absence. The pilot identities are exact named releases and efforts,
not claimed immutable provider snapshots. Arena Agent rows retain exact source labels, effort,
construct, and source-declared intervals, but remain diagnostic preference evidence. AA composites,
ECI rows, and Arena text ratings are also diagnostic. DeepSWE's embedded official leaderboard payload supplies
arithmetic-mean input/output tokens and agent steps for the same four-run task cohort. Those harness
resources enter provisional Efficiency after per-record success adjustment. AA's exact HLE v4.1
facts score for Opus, Sol, Kimi, and GLM on its 2,158-question text-only pass@1 cohort; the published
Fable result is rejected because it explicitly uses an Opus 4.8 fallback. Wall duration and
observed dollar cost remain diagnostic until deployment identity is verified. The fixed workload
hierarchy gives this evidence 4.5% absolute Efficiency coverage; it cannot represent coding as a
whole or unlock Economics.

GDPval-AA v2 contributes exact Max-effort professional-work Elo results for Opus, Sol, Kimi, and
GLM from the 220-task, one-run, blind pairwise public cohort. Source-declared 95% confidence
intervals propagate through comparison sensitivity. Fable's published fallback composite is
rejected. Average turns, output tokens, and calculated cost components remain diagnostic because
they are operational summaries or live-price estimates rather than verified billed task records.

τ³-Banking contributes exact Max-effort pass@1 results for Opus, Sol, Kimi, and GLM from
97 banking-policy tasks repeated five times (485 attempts), with BM25-plus-grep retrieval and
backend-state grading. Fable's fallback-qualified row is rejected. Incomplete token/cost summaries
and the public page's conflicting decode-time units are preserved as diagnostics only; they do not
enter Efficiency or Economics.

AA-LCR contributes exact Max-effort pass@1 results for Opus, Sol, Kimi, and GLM from 100 hard
long-context questions, repeated three times, on the public v4.1.1 cohort. Fable's published
fallback deployment is rejected. The facts retain answer/reasoning token and timing/cost summaries,
but these remain diagnostic because provider token accounting is nonstandard, coverage is incomplete,
and calculated cost is not a deployment- and billing-revision-bound task ledger.

AA-Omniscience contributes the source-defined reliability Index for exact Max-effort Opus, Sol,
Kimi, and GLM rows from the 6,000-question, 42-topic, single-pass v4.1.1 cohort. UMI scores the
published `100 × (correct - incorrect) / 6,000` Index once. Accuracy, attempt rate, hallucination
rate, answer counts, tokens, calculated cost, and upstream time remain reconciled diagnostics; UMI
does not import the AA Intelligence Index's separate 8% accuracy and 4% non-hallucination weights.
Fable's fallback-qualified deployment is rejected.

CursorBench 3.2 solution-correctness scores contribute for Opus, Sol, Kimi, and GLM. Its Fable row
is rejected because Cursor documents invisible Fable-to-Opus routing and the leaderboard does not
prove fallback absence. Published cost/task, tokens/task, and steps/task are retained as diagnostic
benchmark settings, but they do not enter Efficiency or Economics without a compatible binary
success denominator and verified endpoint plus service-tier identity.

## Current limitations

- Opus, Sol, and Kimi have 93.125% Capability coverage across five domains and clear the
  Capability-only coverage/breadth gates. GLM has 79.375% across five domains and also clears those
  two gates; Fable has 8.25% across one. Model-specific partials remain different evidence profiles,
  not one shared ranking.
- Efficiency has only 4.5% absolute coverage; Economics has no ready evidence.
- Fable 5 Max predates the unchanged 2026-06-15 release-window start.
- Scores are cohort-relative; no fixed anchor cohort or formal uncertainty propagation exists.
- Family budgets are documented pilot hypotheses, not empirical decorrelation weights.
- Arena text/style-control is a bounded diagnostic snapshot, not a complete historical extract.
- No frontend, database, scraper, credentials, or live network path is part of the scoring library.

See [PILOT_REPORT.md](PILOT_REPORT.md), [SOURCE_READINESS.md](SOURCE_READINESS.md), and
[SOURCES_AND_LICENSES.md](SOURCES_AND_LICENSES.md) for the audit trail and publication decision.

## Recommended next ingestion task

Close Fable's HLE, τ³-Banking, AA-LCR, and AA-Omniscience cells only with evidence that explicitly
rules out fallback. Then obtain exact attempt-level telemetry for the missing coding families and at least two additional
configured workload categories. Do not broaden the cohort or relax a gate to manufacture a headline.
