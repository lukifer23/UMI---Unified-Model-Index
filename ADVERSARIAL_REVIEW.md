# UMI adversarial review — 2026-08-14

## Overall assessment

**Ready for a narrow, manually reviewed pilot; not ready for public rankings or
bulk ingestion.** The scoring implementation is internally reproducible and now
harder to misuse, but its weights, Value hypotheses, confidence rules, and relative
normalization have not been calibrated against real evidence.

## Weaknesses found and disposition

The genuine pre-ingestion risks were sparse-workload selection gaming,
family-weight/cap conflation, ambiguous partial Overall output, benchmark-label
cohort collisions, silent endpoint drift, single-evaluator dependence, experimental
Value being presented too confidently, and one-dimensional coverage/confidence.
These changed schemas, configuration, scoring, output, validation, and tests.

Several concerns were already substantially handled: zero success was an explicit
worst outcome; small cohorts were provisional; singleton cohorts were unscored;
source-tier consolidation preserved conflicts; exact Pareto ties did not dominate;
Overall headline eligibility existed; and aggregate/constituent members already
shared a family budget. These controls were retained and tested around the new
interfaces.

## Methodology and scoring changes

- Efficiency and Economics now use six configured workload-class budgets and
  expose represented and weighted workload coverage.
- Capability separates domain weights, family weights, family caps, and benchmark
  representation weights. Incompatible evaluation cohorts share representation
  budgets but normalize separately.
- The available-evidence calculation is explicitly a
  `partial_overall_estimate`; `headline_overall` is null until eligibility passes.
- Value is explicitly experimental, configured in `config/value.yaml`, and has a
  bounded formula-sensitivity command.
- Coverage now distinguishes domains, families, workload classes, evidence tier,
  and source-organization diversity.
- Confidence remains rule based and returns reasons. Single-source evidence caps
  High confidence; insufficient Capability breadth caps confidence at Low.
- Every result identifies its model cohort, evaluation date, normalization version,
  formula version, and configuration fingerprint.

## Schema and validation changes

Models can preserve immutable snapshot and API endpoint IDs. Measurements can
preserve model snapshot, evaluation date, compatibility cohort key, sample/task/
trial counts, pass@k, standard error, and confidence intervals. Provenance can
identify evaluator, harness owner, run executor, raw artifact availability,
reproducibility, and configuration verification.

Validation rejects family/domain/reference errors and snapshot collisions. It
warns when a record lacks a cohort key, benchmark/harness version, snapshot/date,
raw artifact, evaluator, or verified configuration. `SOURCE_READINESS.md` is the
ingestion gate; missing facts may not be invented to silence it.

## Adversarial tests

The suite now covers sparse-workload gaming, ambiguous missing-component output,
snapshot collision, incompatible harness cohorts, 1%/0% success behavior,
single-evaluator confidence caps, and Value sensitivity. Existing tests continue
to cover family double-counting, source-tier conflicts, outliers/zero MAD,
small/singleton cohorts, ties, correlations, Pareto dominance, CLI schemas, and
determinism.

## Validation report

- Methodology/API contract: verified against `METHODOLOGY.md`; no scoring decision
  introduced without a documented rule.
- Weight totals and family references: validated by typed configuration and tests.
- Partial/headline separation: verified by serialization test and CLI smoke output.
- Cohort identity: deterministic SHA-256-derived ID verified in repeatable output.
- Synthetic calculations: recomputed through library and CLI paths; 35 tests pass
  with 95% line coverage.
- Static checks: Ruff and strict mypy pass.
- Source/data claims: no real-data claims are made. Synthetic readiness warnings are
  expected because fixtures do not impersonate retained real artifacts.

## Known remaining failure modes

- Scores still move when cohort membership changes; no frozen scale or anchor model
  exists.
- Family/workload weights are reasoned defaults, not empirically calibrated.
- Confidence does not propagate sampling uncertainty, rank sensitivity, or source
  dependence beyond an organization-count cap.
- Cohort keys are curated identifiers, not a canonical hash of every evaluation
  setting; ingestion review remains necessary.
- Very low nonzero success rates can still have large leverage. They are log
  transformed but deliberately not clipped.
- Exact tied scores share ranks, but no documented near-tie tolerance exists.
- Economics still requires genuinely comparable observed cost-per-success baskets;
  advertised prices cannot substitute.
- Value formulas can agree on synthetic fixtures yet diverge in real cohorts. No
  formula is validated as a user-utility model.
- Pareto analysis remains dimension-specific and does not compare unlike workload
  categories; multi-dimensional tolerance is unresolved.

## Exact next task

Build one manual Artificial Analysis snapshot adapter and source registry for four
to six configurations. Retain the dated raw capture, map only measurements with
identifiable model snapshots and compatible harness/workload definitions, run the
source-readiness gate, and publish a data-quality report before calculating any
pilot score. Treat missing successful-task cost or incompatible settings as
unscored—not as values to infer.
