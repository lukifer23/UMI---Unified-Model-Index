# RootCauseBench v3 diagnostic evidence review

This deterministic offline review validates a licensed, frozen final-trial ledger. It is not a UMI score and does not change UMI coverage.

- source: [https://github.com/edgedelta/root-cause-bench](https://github.com/edgedelta/root-cause-bench)
- pinned commit: `0c3c476e4627978dc54b5c047fd488d40561b4e5`
- license / retained scope: `Apache-2.0` / `full_artifact`
- final trials: `2808` across `26` routes
- profile: `terminus-2`, `3` attempts/scenario, `1800s` timeout

## Observed final-trial diagnostics

Each resource value is the total across final trials divided by successful final trials. `CostUSD` is source-reported router cost, never provider billing.

| Candidate pilot | Source route | Trials | Passed | Pass rate | Reward | Duration/success (s) | Router cost/success ($) |
|---|---|---:|---:|---:|---:|---:|---:|
| `claude-fable-5-max` | `openrouter/anthropic/claude-fable-5` | 108 | 104 | 96.3% | 0.968 | 192.2 | 0.8792 |
| `claude-opus-5-max` | `openrouter/anthropic/claude-opus-5` | 108 | 106 | 98.1% | 0.981 | 137.7 | 0.3336 |
| `gpt-5.6-sol-max` | `openrouter/openai/gpt-5.6-sol` | 108 | 104 | 96.3% | 0.967 | 109.6 | 0.2331 |
| `kimi-k3-max` | `openrouter/moonshotai/kimi-k3` | 108 | 107 | 99.1% | 0.991 | 252.4 | 0.1534 |
| `glm-5.2-max` | `openrouter/z-ai/glm-5.2` | 108 | 106 | 98.1% | 0.981 | 445.8 | 0.1136 |

## Why no UMI score is emitted

- `missing-explicit-inference-effort`
- `missing-verified-exact-deployment`
- `missing-provider-billing-reconciliation`
- `missing-request-and-retry-history-residuals`

The source records a route and agent, not an effective Max effort or verified deployment. Its final-trial router costs are diagnostic, and it does not retain request/retry history sufficient to prove an all-attempt resource or billing ledger.
