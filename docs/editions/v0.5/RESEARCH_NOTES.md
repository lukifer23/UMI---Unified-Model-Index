# UMI Public v0.5 expansion research

Same frozen Epoch zip as v0.4. No new downloads. No paid requests.

Complete common-core (all ten series, 8+ anchors):

| Config ID | Decision |
|---|---|
| claude-opus-5_max | Keep; v0.4 reproduction |
| claude-fable-5_max | Keep; composite |
| gpt-5.6-sol_max | Keep |
| kimi-k3_max | Keep |
| glm-5.2_max | Keep |
| gemini-3.6-flash_high | **Accept** as exact high-effort entity |
| gpt-5.4-2026-03-05_xhigh | **Accept** as exact xhigh entity |

Near-miss `_max` rows missing only WeirdML: `gpt-5.6-terra_max`, `gpt-5.6-luna_max`,
`claude-sonnet-5_max`, `claude-opus-4-8_max`. Rejected; no imputation.

No other `_max` row has DeepSWE mini-swe-agent plus the rest of the common core.

Named candidates requested by the v0.5 spec, audited and not scored:

| Config IDs | Present | Missing | Decision |
|---|---:|---|---|
| `grok-4.5_high` | 8/10 | `epoch-weirdml`, `weirdml-cost-per-run` | Diagnostic certificate only |
| `gemini-3.1-pro-preview`, `gemini-3.1-pro-preview_high` | 9/10 | `weirdml-cost-per-run` | Diagnostic certificate only. Unsuffixed WeirdML cost 1.36 exists and is excluded by the Access high-effort suffix panel. Changing that panel would rescore every published Access point. |
