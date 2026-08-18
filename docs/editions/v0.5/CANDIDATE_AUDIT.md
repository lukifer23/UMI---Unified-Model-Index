# UMI Public v0.5 candidate audit

Primary targets:

| Candidate | Common-core | Missing | State |
|---|---|---|---|
| `grok-4.5-high` | 8/10 | WeirdML accuracy, WeirdML cost | `insufficient_common_support` |
| `gemini-3.1-pro-preview` | 9/10 | high-effort WeirdML cost | `insufficient_common_support` |

Intake only: `grok-4.6-xai-high`, `gpt-5.5-xhigh`, `qwen3.8-max`, `muse-spark-1.1`.

Rules:

- Do not call Grok 4.5 “Max”.
- Do not infer Gemini thinking level from “Preview”.
- Do not shrink the common core to admit a candidate.
- Do not refit anchors when a candidate is displayed.
- Grok CursorBench is contamination-risk diagnostic by default.

A new Epoch Benchmarking Hub zip was acquired on 2026-08-17 as
`data/sources/acquisitions/v05-epoch-probe-2026-08-17/` (SHA-256
`7284f0a202e0d3396452ba57e84b0bc3ce812828826043eea2bb8c2b4f7f47e9`). It is **not**
the scoring artifact. The probe still lacks `grok-4.5_high` WeirdML accuracy/cost and
lacks a high-effort WeirdML cost suffix for `gemini-3.1-pro-preview` (unsuffixed cost
1.36 remains excluded). `grok-4.5_unknown` is not High. The August 14 zip remains the
scored snapshot.

Command:

```bash
PYTHONPATH=. uv run --no-sync umi edition --edition v0.5 candidates
```
