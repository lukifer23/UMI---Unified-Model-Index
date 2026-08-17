# UMI Public v0.4 source research

Retrieval date: 2026-08-17. No paid requests. Scoring remains offline. The frozen Epoch archive is
`data/sources/v0.3/epoch-benchmark-data-2026-08-14.zip` (SHA-256 of the zip as committed).

| Source | Official URL | Frozen material | License / redistribution | Pilot rows | Anchor rows | Decision |
|---|---|---|---|---|---|---|
| Epoch chess puzzles | Epoch Benchmarking Hub | `chess_puzzles.csv` | Epoch archive CC BY 4.0 | All five `_max` | 158 | **Accept** Capability / general reasoning |
| DeepSWE v1.1 via Epoch Hub | https://deepswe.datacurve.ai/ | `deepswe_external.csv` `mini-swe-agent` | Epoch archive CC BY 4.0; DeepSWE facts also cited separately | All five Max configs | 50 | **Accept** Capability (software) and Operational Efficiency (output tokens, steps). Cost diagnostic only |
| DeepSWE official facts | https://deepswe.datacurve.ai/artifacts/v1.1/trials.json | Reviewed facts `deepswe-reviewed-facts-2026-08-13.yaml`; ledger not redistributed | Facts and citations only | All five | 5 | Corroborates Epoch Pass@1 / tokens / steps. Fable cost 432/436 **reject** as complete Access series |
| AA SciCode via Epoch extract | https://artificialanalysis.ai/evaluations/scicode | `scicode_external.csv` | Epoch archive CC BY 4.0 | All five `_max`; Fable Name is the Opus 4.8 fallback composite | 128 | **Accept** Capability / software for the Fable composite entity |
| WeirdML | https://htihle.github.io/weirdml.html | `weirdml_external.csv` | Epoch archive CC BY 4.0 | All five `_max` | 162 accuracy; 50 high-effort cost | **Accept** Capability / agentic and Access Economics (high-effort cost panel) |
| Epoch GPQA Diamond | Epoch simple-evals extract | `gpqa_diamond.csv` | Epoch archive CC BY 4.0 | All five `_max` | 260 | **Accept** Capability / math-science |
| Epoch OTIS Mock AIME 2024–2025 | Epoch Benchmarking Hub | `otis_mock_aime_2024_2025.csv` | Epoch archive CC BY 4.0 | All five `_max` | 235 | **Accept** Capability / math-science |
| Epoch CritPt | Epoch Benchmarking Hub | `critpt_external.csv` | Epoch archive CC BY 4.0 | All five `_max`; Fable Name is the Opus 4.8 fallback composite | 139 | **Accept** Capability / math-science for the Fable composite. Cost column empty for the five |
| LiveBench (Epoch extract) | https://livebench.ai/ | `live_bench_external.csv` (64 rows) | Epoch archive | **Zero** of the five 2026 Max pilots | 64 older models | Reject for common-core |
| Epoch HLE | Epoch extract | `hle_external.csv` | Epoch archive | None of the five `_max` IDs | — | Reject for common-core |
| SimpleQA Verified | Epoch extract | `simpleqa_verified.csv` | Epoch archive | Missing `claude-fable-5_max` (has `_xhigh`) | 74 | Reject: not all five exact Max IDs |
| Epoch CursorBench extract | Epoch extract | `cursorbench_external.csv` | Epoch archive | Missing `kimi-k3_max` | 31 | Reject: not all five |
| AA HLE, τ³, LCR, Omniscience, Terminal-Bench, GDPval reviewed facts | https://artificialanalysis.ai/ | Five-row reviewed facts only | Facts and citations | All five if Fable is the composite product | **5** | Reject for headline: anchor panel < 8 on the same harness |
| CursorBench 3.2 reviewed facts | https://cursor.com/cursorbench | Five-row reviewed facts | Facts and citations | All five if Fable is composite | **5** | Reject for headline: anchor panel < 8 |
| Official tariffs | lab release facts | Five price cards | Facts and citations | All five | **5** | Reject for headline baskets: need 8+ official cards |
| AA Intelligence Index / Epoch ECI | public composites | Existing diagnostic extracts | — | — | — | Reject: aggregate plus constituents |

The earlier note that GPQA / SciCode / CritPt lacked the five-set was wrong. Those Epoch members
do contain every exact `_max` identifier. What they lacked under v0.3 was a *plain* Fable Max
identity: SciCode and CritPt name the Opus 4.8 fallback. v0.4 scores that evidence against the
composite Fable product.

Conclusion: ten frozen series qualify for the first Public common core. Context reliability,
language / instruction following, interactive latency, billed Economics, and complete DeepSWE
cost do not.
