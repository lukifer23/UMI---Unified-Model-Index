# v0.3 sources, attribution, and redistribution

The machine-readable authority is `data/sources/registry.yaml`. This document explains the policy in
human-readable form. UMI's MIT license does not override upstream terms.

| Source | Frozen material | Upstream revision | License / use basis | Redistribution |
|---|---|---|---|---|
| Artificial Analysis | Manually reviewed public index, atomic HLE v4.1, GDPval-AA v2, and τ³-Banking facts | `manual-public-facts-2026-08-14`; `reviewed-hle-v4.1-2026-08-14`; `public-page-2026-08-15`; `tau3-banking-public-page-2026-08-15` | Terms-governed; API documentation and terms require attribution and govern reuse | Facts and citations only; no API payload, task content, work products, or page copy |
| Cursor | Manually reviewed CursorBench 3.2 score, cost/task, tokens/task, and steps/task facts | `cursorbench-3.2-public-page-2026-08-14` | Terms-governed; no redistribution right assumed | Facts and citations only; no page payload, task content, or chart artwork |
| Epoch ECI | Official `eci_benchmarks.csv` | `dab4f8ac0d14ec7022da01684fa2c707f73749eb` | Epoch attribution recorded; `eci-public` implementation is MIT licensed | Official public CSV frozen with citation |
| Epoch Benchmarking Hub | Complete official `benchmark_data.zip`; GPQA Diamond, SciCode, and CritPt adapted | semantic member-content SHA-256 `2b818e5b…7f009`; frozen container SHA-256 `35a7c21b…a18b` | CC BY 4.0 with Epoch attribution; individual benchmark questions remain subject to creator rights | Full official data archive retained; benchmark questions are not separately republished |
| LM Arena | Dataset Viewer JSON for `agent` and a bounded `text_style_control` page | `08dd89df7a8aa9df2ead3799f6422af4ad2e97a7` | CC BY 4.0 | Artifact retained with attribution |
| DeepSWE | Manually reviewed v1.1 leaderboard facts | leaderboard generated `2026-08-13T16:11:55.708636Z` | No leaderboard-data redistribution license established | Facts and citations only; no gated tasks or trajectories |

Attribution:

- Artificial Analysis public model, HLE, GDPval-AA v2, τ³-Banking, methodology, and API documentation:
  https://artificialanalysis.ai/evaluations/humanitys-last-exam and
  https://artificialanalysis.ai/evaluations/gdpval-aa and
  https://artificialanalysis.ai/evaluations/tau3-banking and
  https://artificialanalysis.ai/methodology/intelligence-benchmarking and
  https://artificialanalysis.ai/data-api/docs
- CursorBench 3.2 leaderboard and methodology:
  https://cursor.com/cursorbench and https://cursor.com/blog/cursorbench
- Epoch AI ECI data and documentation: https://github.com/epoch-research/eci-public
- Epoch AI Benchmarking Hub and methodology: https://epoch.ai/benchmarks/about
- LM Arena historical leaderboard dataset:
  https://huggingface.co/datasets/lmarena-ai/leaderboard-dataset
- DeepSWE v1.1 leaderboard by Datacurve: https://deepswe.datacurve.ai/

Checksums are validated before source readiness passes. A changed artifact, missing license field,
missing attribution, or upstream-revision mismatch is a hard source-validation failure.
