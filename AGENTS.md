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

Run `uv run pytest`, `uv run ruff check .`, and `uv run mypy` before handing off changes.

