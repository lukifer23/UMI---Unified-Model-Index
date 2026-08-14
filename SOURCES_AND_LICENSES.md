# v0.3 sources, attribution, and redistribution

The machine-readable authority is `data/sources/registry.yaml`. This document explains the policy in
human-readable form. UMI's MIT license does not override upstream terms.

| Source | Frozen material | Upstream revision | License / use basis | Redistribution |
|---|---|---|---|---|
| Artificial Analysis | Manually reviewed public facts | `manual-public-facts-2026-08-14` | Terms-governed; API documentation requires attribution and directs redistribution questions to its terms | Facts and citations only; no API payload or page copy |
| Epoch ECI | Official `eci_benchmarks.csv` | `dab4f8ac0d14ec7022da01684fa2c707f73749eb` | Epoch attribution recorded; `eci-public` implementation is MIT licensed | Official public CSV frozen with citation |
| Epoch Benchmarking Hub | Complete official `benchmark_data.zip`; GPQA Diamond adapted | semantic member-content SHA-256 `2b818e5b…7f009`; frozen container SHA-256 `35a7c21b…a18b` | CC BY 4.0 with Epoch attribution; individual benchmark questions remain subject to creator rights | Full official data archive retained; benchmark questions are not separately republished |
| LM Arena | Dataset Viewer JSON for `agent` and a bounded `text_style_control` page | `08dd89df7a8aa9df2ead3799f6422af4ad2e97a7` | CC BY 4.0 | Artifact retained with attribution |
| DeepSWE | Manually reviewed v1.1 leaderboard facts | harness repo `435ee89ec2f2e2289f33b0da4f992f0b7b7266b9` | No leaderboard-data redistribution license established | Facts and citations only; no gated tasks or trajectories |

Attribution:

- Artificial Analysis public model, methodology, and API documentation:
  https://artificialanalysis.ai/data-api/docs
- Epoch AI ECI data and documentation: https://github.com/epoch-research/eci-public
- Epoch AI Benchmarking Hub and methodology: https://epoch.ai/benchmarks/about
- LM Arena historical leaderboard dataset:
  https://huggingface.co/datasets/lmarena-ai/leaderboard-dataset
- DeepSWE v1.1 leaderboard by Datacurve: https://deepswe.datacurve.ai/

Checksums are validated before source readiness passes. A changed artifact, missing license field,
missing attribution, or upstream-revision mismatch is a hard source-validation failure.
