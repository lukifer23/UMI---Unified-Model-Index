# UMI build plan

## Objective

Build an auditable current-release index for exact model configurations: exact named release or
immutable model snapshot plus inference effort, and provider/endpoint/tier when deployment affects the
measurement. It must separately measure capability, success-adjusted efficiency, and
success-adjusted economics, then emit a unified headline only when all evidence gates pass.

Version 1 covers text/reasoning, coding, tool use, browser/computer use, and long-horizon
agents. Multimodal, safety, and enterprise controls need separate typed domains and cannot be
silently folded into this score.

## Current state

v0.3 is a good fail-closed pilot. It has immutable records, frozen artifacts, exact
crosswalks, source/license registry, offline adapters, overlap controls, hierarchical
coverage, per-record success adjustment, fingerprints, diagnostics, and headline gates.

It does not yet support a public UMI. The current five-model pilot has 48 of 75 configured
Capability cells ready. Opus, Sol, Kimi, and GLM now span five domains and clear the Capability-only
coverage gate (100%, 100%, 100%, and 86.25% respectively), while Fable remains at 8.25%
because fallback-qualified evidence is rejected. Efficiency is still 4.5% DeepSWE-only coverage
and Economics has no ready workload evidence. Weights remain hypotheses, normalization remains
cohort-relative, and source-bound uncertainty is deterministic endpoint sensitivity rather than a
fully calibrated probabilistic model. Lab claims are first-class diagnostics but mostly lack an
independent, cohort-identical comparison.

## Permanent rules

- Keep raw source artifacts, literal labels, crosswalk decisions, selected IDs, conflicts,
  revisions, and licenses through every report.
- Never infer a missing snapshot, effort, endpoint, cohort, harness, resource mean, success
  rate, or price. Incompatible evidence is diagnostic or rejected.
- Derive resource and cost per success on its original record before selection; fast failure
  never wins.
- Keep Epoch ECI, Artificial Analysis indices, Arena aggregates, lab claims, and atomic task
  results as distinct typed signals. Never double-count a composite and its constituents.
- Partial outputs cannot receive a headline score, ordinal rank, or leaderboard styling.
- Update `METHODOLOGY.md` with every formula, weight, threshold, coverage, confidence, or
  readiness change; add adversarial tests and regenerate schemas in the same change.

## Evidence layers

| Layer | Examples | UMI treatment |
|---|---|---|
| Atomic task evidence | HLE, GPQA, ARC-AGI-2, DeepSWE, Terminal-Bench, CursorBench, GDPval-AA, tau3, METR | Score only after exact profile/readiness/overlap review. |
| Preference evidence | LM Arena text, coding, webdev, search, document, Agent Arena | A bounded preference domain, never a universal capability proxy. |
| Composite references | Epoch ECI; AA Intelligence, Coding, Agentic indices | Diagnostic/calibration evidence by default; never a second vote. |
| Claims and deployment facts | Model cards, lab release claims, API and price cards | Claims are audited; prices remain reference facts until tied to measured task telemetry. |

Add typed, fingerprinted evaluation profiles: benchmark/split, harness, scaffold/agent and
version, tools, prompt/context/token limits, effort, sampling/retry/pass@k, endpoint/tier,
evaluator, execution date, and task/trial counts. Add deployment profiles for API identity,
region, billing revision, cache/tool prices, and effective dates.

Add reviewed `source_assessments` and `claim_calibration` datasets. They record claim text,
protocol, independence, reproducibility, overlap, contamination/freshness concern, evidence,
and accepted/diagnostic/rejected/superseded disposition. Calibration reports compatible
claim-versus-external error only; it never generalizes from sparse or incomparable results.

## Score design

Retain hierarchical domain → family → representation budgets. Calibrate weights only through a
documented study linking a user-job taxonomy, construct mapping, measured dependence, source and
family ablations, and (where possible) independent user-task outcomes. If that cannot justify a
single baseline, retain named scenarios and withhold the singular score.

Build six versioned workload baskets: coding, research/analysis, tool use, browser/computer use,
general interaction, and long horizon. Each needs an explicit success definition and attempt ledger
with input/output/reasoning/cache-read/cache-write/tool units, wall time, turns, retries, errors,
success, and observed bill. A deterministic dated pricing replay may be reported as modeled cost,
but may never silently replace observed cost.

Maintain separate interactive round-turn and autonomous task-run profiles. Publish physical metrics
and workload frontiers alongside component scores. Add atomic uncertainty propagation, rank
intervals, near-tie bands, pairwise superiority, leave-source-out movement, and sensitivity gates.
Use a frozen anchor panel and versioned release cohorts so new data creates a new report rather than
silently rewriting history.

## Delivery phases

### Phase 0 — restore release verification

Repair the currently reproduced Python 3.14 packaging failure: the editable Hatch `.pth` is
underscore-prefixed and ignored by Python. Tests formerly passed only because the checkout was on
`sys.path`; the installed CLI and isolated import fail. Add supported-Python CI, isolated wheel
install smoke outside the checkout, all CLI smokes, deterministic rebuild/diff, and publication
assertions. Do not claim `>=3.11` support without this matrix.

Exit: clean install/import and every documented offline CLI flow work; v0.3 rebuilds
deterministically with all headlines null.

### Phase 1 — approve v1 policy/contracts

Extend methodology and schemas for evaluation/deployment profiles, source assessment, claim
calibration, source independence/freshness, uncertainty/stability, anchors, and distinct
round-turn versus autonomous economics. Create a decision log for scope, portfolio, user-job
weights, success criteria, update cadence, licensing, and disclosure.

Exit: every source type has a typed admission checklist; adapters cannot guess material facts.

### Phase 2 — evidence intake factory

Create capture manifests (URL, revision/date, checksum, terms, attribution, completeness), common
offline adapter conformance tests, and reports for readiness, crosswalk coverage, profile matrix,
overlap, missing telemetry, licenses, freshness, and claim calibration.

Exit: no source scores without retained artifact, rights decision, exact identity, compatible
profile, overlap disposition, and adversarial tests.

### Phase 3 — capability portfolio

Ingest one domain at a time: first HLE, GPQA Diamond/CritPt, and a context/reliability family;
then ARC-AGI-2 as a dedicated abstract-reasoning representation; then DeepSWE, Terminal-Bench,
CursorBench, and one fresh/live coding suite with model-plus-agent identity; then GDPval-AA, tau3,
METR, and Arena as distinct constructs. ECI/AA remain overlap and calibration diagnostics.

Exit: three or more Capability domains have diversified ready atomic evidence and pass precommitted
breadth, overlap, and uncertainty review; otherwise publish only a partial report.

### Phase 4 — real Efficiency and Economics

Acquire or produce licensed, reproducible attempt telemetry for exact deployments across the
configured workload coverage. Implement the resource ledger and pricing replay; red-team zero or
sparse success, non-mean summaries, retries, cache writes, tools, long-context price tiers, and
endpoint changes.

Exit: all component inputs are comparable per-success measurements; price cards alone unlock none.

### Phase 5 — calibrate and harden

Run the documented weight/dependence study, uncertainty propagation, rank stability analysis,
anchor/release versioning, and independent adversarial review. Red-team double-counting,
effort/scaffold mismatch, cohort averaging, cross-record success joins, stale endpoints, and
partial-to-headline presentation leaks.

Exit: an external reviewer can recreate scores, rank intervals, and every reason a score was gated.

### Phase 6 — versioned public release

Publish signed manifest, rights-compliant data package, methodology, changelog, and per-model
evidence cards. Present Capability, coding-agent effectiveness, interactive cost, autonomous task
economics, reliability/context, preference, and experimental Value separately. The conditional UMI
headline appears only for eligible configurations and always includes coverage, confidence, rank
interval, sources, alternatives, fingerprints, and as-of date.

## Definition of done

UMI may claim a unified score only when the installed product works in a clean environment; frozen
evidence is reproducible and legally usable; composite sources cannot double-count atomic evidence;
all three components meet their configured representative coverage; uncertainty and rank stability
are disclosed; lab claims are audited against compatible external evidence; and a skeptical third
party can recreate the score or see precisely why it was withheld.
