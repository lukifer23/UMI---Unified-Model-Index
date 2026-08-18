# UMI Public v0.4 processed index

`release_class`: `historical_experimental_point_score`.

Canonical scored payload: `processed/model-scores.json`.
This edition publishes five point scores. It does not emit a governed certificate,
partial intervals, candidate audits, or a blocker report. Those surfaces belong to
v0.5.

Do not rewrite `model-scores.json`, `common-core.json`, or `rejected-evidence.json`.
Their SHA-256 values are frozen in `tests/test_v04_legacy_freeze.py`.
