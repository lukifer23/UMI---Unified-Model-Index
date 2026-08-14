# Instructions for coding agents

1. `METHODOLOGY.md` is the authority for every scoring decision.
2. Never silently change weights, formulas, thresholds, or normalization behavior. Update the methodology and configuration together.
3. Do not invent model, benchmark, price, or task data.
4. Preserve source provenance and raw source records through every derived result.
5. Mark synthetic data conspicuously and keep it in test fixtures.
6. Add or update tests whenever scoring behavior changes.
7. Prefer transparent, composable implementation over cleverness.
8. If methodology is ambiguous, document the ambiguity instead of making an invisible assumption.
9. Do not build the frontend ahead of the data and scoring foundation.
10. Keep external data ingestion separate from scoring logic.
11. Never serialize a partial Overall estimate under an ambiguous headline field.
12. Never normalize measurements together solely because labels match; require compatible cohort keys and immutable model snapshots.
13. Report measurement count, family breadth, workload breadth, and source-organization diversity separately.
14. Treat Value as experimental and identify its formula in every output.
15. Before real-data ingestion, run source-readiness validation and retain an inspectable source capture or artifact reference.

Run `uv run pytest`, `uv run ruff check .`, and `uv run mypy` before handing off changes.
