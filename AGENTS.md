# Instructions for coding agents

1. `METHODOLOGY.md` is authoritative. Update it before or with any formula, weight, threshold,
   normalization, coverage, eligibility, readiness, or confidence change.
2. Never invent model, benchmark, price, cost, token, latency, success, identity, or provenance data.
3. Preserve immutable raw records, source artifact references, selected record IDs, and conflict
   diagnostics through derived output.
4. Keep synthetic data conspicuously labeled and isolated in fixtures; never present it as a real
   ranking.
5. Treat the model snapshot/inference effort/deployment—not the marketing family—as the scored
   entity. Reject snapshot and deployment mismatches.
6. Never normalize or average records because labels resemble each other. Require one explicit,
   compatible scoring cohort; retain additional cohorts as diagnostic.
7. Derive success-adjusted resources per record before provenance selection and consolidation. Never
   pair a numerator with another record's success rate, and never reward fast failure.
8. Calculate coverage against the complete configured hierarchy. Presence of one representation,
   family, workload, or low-weight metric is not full coverage.
9. Never serialize a partial estimate as a headline. A headline requires Capability, Efficiency, and
   Economics plus all configured coverage, breadth, date, and readiness gates.
10. Treat Value as experimental. Keep named hypotheses distinct and expose rank instability.
11. Keep confidence rule-based with explicit reasons. Provisional, conflicting, single-source, sparse,
    vendor-only, or unready evidence must apply the documented caps.
12. Make correlations direction- and cohort-safe, and Pareto frontiers workload/cohort specific. Do
    not emit universal conclusions from incomparable series.
13. Every scored input or scoring-configuration change must change `scored_data_fingerprint`; input
    order must not. Never add dynamic timestamps to fingerprints.
14. Reject non-finite source values. Internal positive infinity is allowed only as the zero-success
    sentinel and must be consumed before JSON serialization.
15. Keep configuration live: every scoring-relevant field must affect behavior or be removed.
16. Add adversarial tests for every scoring change, including missing data, cohort collisions,
    readiness, aliases, zero success, coverage, eligibility, confidence, and fingerprints.
17. Regenerate `schemas/` after Pydantic changes. JSON Schema is the machine-readable authority;
    `DATA_SCHEMA.md` is explanatory and must agree with it.
18. Keep ingestion adapters, scoring logic, and presentation separate. Do not add scraping, a frontend,
    a database, or model-specific scoring exceptions without an explicit milestone.
19. Prefer small typed functions and clear diagnostics over opaque statistical machinery. Document
    unresolved methodology instead of hiding an assumption.
20. Before handoff run `uv run pytest`, coverage, `uv run ruff check .`, strict `uv run mypy`, and all
    CLI smoke commands. Do not claim checks that were not executed.
21. Keep acquisition separate from ingestion. Adapters must be deterministic, offline, and consume
    frozen artifacts; no credentials, scraping, or runtime HTTP belongs in scoring.
22. Require exact model, release, effort, and relevant deployment crosswalks. Never infer omitted
    effort or map fallback/composite aliases to plain configurations.
23. Validate licenses, attribution, redistribution scope, revisions, and checksums. Unknown
    redistribution rights mean facts-and-citations only.
24. Keep structural dataset validation, accepted scored-bundle validation, and strict complete-audit
    validation separate. Diagnostic evidence must not block a score it does not feed.
25. Build comparison certificates only from a revalidated `ScoringBundle` and the common-evidence
    engine. Fingerprint canonical contents without timestamps; abstain rather than omit failed
    comparability bindings.
