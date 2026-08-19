# UMI Public v0.5 evidence blocker report

This report documents evidence that is genuinely unavailable in the frozen public
archive. It does not invent scores, impute missing cells, or lower gates.

Edition: `umi-public-v0.5`. Zip SHA-256: `35a7c21ba7d535514ebcf9bbe7b8265d2e2da40ef6b1fa63fe49323c3395a18b`.
Status: `published_with_documented_blockers`. Governed partial values remain published for complete common-core rows; no Overall headline is published.

| Blocker | Affected | Missing series | Why it fails | What would resolve it |
|---|---|---|---|---|
| `candidate-grok-4.5-high` | `grok-4.5-high` | `epoch-weirdml`, `weirdml-cost-per-run` | Frozen Epoch extract is missing required common-core series for this exact identity | Same-zip rows for every missing series at the exact config/effort identity, including a high-effort WeirdML cost suffix if Access is required |
| `candidate-gemini-3.1-pro-preview` | `gemini-3.1-pro-preview` | `weirdml-cost-per-run` | Frozen Epoch extract is missing required common-core series for this exact identity | Same-zip rows for every missing series at the exact config/effort identity, including a high-effort WeirdML cost suffix if Access is required |
| `near-miss-gpt-5.6-terra-max` | `gpt-5.6-terra-max` | `epoch-weirdml`, `weirdml-cost-per-run` | Frozen Epoch extract is missing required common-core series for this exact identity | Same-zip rows for every missing series at the exact config/effort identity, including a high-effort WeirdML cost suffix if Access is required |
| `near-miss-gpt-5.6-luna-max` | `gpt-5.6-luna-max` | `epoch-weirdml`, `weirdml-cost-per-run` | Frozen Epoch extract is missing required common-core series for this exact identity | Same-zip rows for every missing series at the exact config/effort identity, including a high-effort WeirdML cost suffix if Access is required |
| `near-miss-claude-sonnet-5-max` | `claude-sonnet-5-max` | `epoch-weirdml`, `weirdml-cost-per-run` | Frozen Epoch extract is missing required common-core series for this exact identity | Same-zip rows for every missing series at the exact config/effort identity, including a high-effort WeirdML cost suffix if Access is required |
| `near-miss-claude-opus-4-8-max` | `claude-opus-4-8-max` | `epoch-weirdml`, `weirdml-cost-per-run` | Frozen Epoch extract is missing required common-core series for this exact identity | Same-zip rows for every missing series at the exact config/effort identity, including a high-effort WeirdML cost suffix if Access is required |
| `series-deepswe-mean-cost` | `claude-fable-5-max` | `deepswe-mean-cost` | Official DeepSWE v1.1 cost is observed on 432 of 436 scored Fable attempts and cannot enter a complete all-attempt Access series | Complete Fable cost denominator or another all-five billed/calculated series |
| `construct-context-reliability` | `edition-scope` | `context_reliability_and_factual_discipline` | No frozen public series has all five exact Max identities and an 8+ same-harness anchor panel for context reliability | A frozen same-harness extract with all five pilots plus 8+ anchors |
| `construct-language-instruction` | `edition-scope` | `language_data_and_instruction_following` | No frozen public series has all five exact Max identities and an 8+ same-harness anchor panel for language, data, or instruction following | A frozen same-harness extract with all five pilots plus 8+ anchors |
| `construct-interactive-latency` | `edition-scope` | `interactive_service_responsiveness` | No frozen public series has all five exact Max identities and an 8+ same-extract anchor panel for interactive service latency | A frozen same-harness latency extract with all five pilots plus 8+ anchors |
| `construct-billed-economics` | `edition-scope` | `provider_billing_record` | No frozen all-five 8+ billed ledger exists. Source-reported WeirdML cost is Access Economics, not observed provider billing | An admissible all-five billed task ledger with exact deployment identity |
| `construct-hierarchical-bootstrap` | `edition-scope` | `attempt_level_residuals` | Frozen extracts are configuration-level means without attempt residuals, so hierarchical bootstrap remains unpublished | Redistributable attempt-level residuals for every headline series |

Every blocker has `umi_public: null`. Named candidates and `_max` near-misses stay
off the headline. Access keeps the high-effort suffix panel; unsuffixed WeirdML
cost is not admitted.

## candidate-grok-4.5-high

- affected model: `grok-4.5-high`
- required identity: exact high configuration on all ten common-core series
- missing series: epoch-weirdml, weirdml-cost-per-run
- sources investigated: Epoch weirdml_external.csv; Epoch remaining common-core members; WeirdML public leaderboard citation
- URLs investigated: https://epoch.ai/data/benchmark_data.zip; https://htihle.github.io/weirdml.html; https://epoch.ai/benchmarks/about
- reason: Frozen Epoch extract is missing required common-core series for this exact identity
- resolving evidence: Same-zip rows for every missing series at the exact config/effort identity, including a high-effort WeirdML cost suffix if Access is required
- umi_public: null

## candidate-gemini-3.1-pro-preview

- affected model: `gemini-3.1-pro-preview`
- required identity: exact high configuration on all ten common-core series
- missing series: weirdml-cost-per-run
- sources investigated: Epoch weirdml_external.csv including unsuffixed Cost per run=1.36; gemini-3.1-pro-preview_high (incomplete suffix row); WeirdML public leaderboard citation
- URLs investigated: https://epoch.ai/data/benchmark_data.zip; https://htihle.github.io/weirdml.html; https://epoch.ai/benchmarks/about
- reason: Frozen Epoch extract is missing required common-core series for this exact identity
- resolving evidence: Same-zip rows for every missing series at the exact config/effort identity, including a high-effort WeirdML cost suffix if Access is required
- umi_public: null

## near-miss-gpt-5.6-terra-max

- affected model: `gpt-5.6-terra-max`
- required identity: exact max configuration on all ten common-core series
- missing series: epoch-weirdml, weirdml-cost-per-run
- sources investigated: Epoch common-core members; Epoch weirdml_external.csv
- URLs investigated: https://epoch.ai/data/benchmark_data.zip; https://htihle.github.io/weirdml.html
- reason: Frozen Epoch extract is missing required common-core series for this exact identity
- resolving evidence: Same-zip rows for every missing series at the exact config/effort identity, including a high-effort WeirdML cost suffix if Access is required
- umi_public: null

## near-miss-gpt-5.6-luna-max

- affected model: `gpt-5.6-luna-max`
- required identity: exact max configuration on all ten common-core series
- missing series: epoch-weirdml, weirdml-cost-per-run
- sources investigated: Epoch common-core members; Epoch weirdml_external.csv
- URLs investigated: https://epoch.ai/data/benchmark_data.zip; https://htihle.github.io/weirdml.html
- reason: Frozen Epoch extract is missing required common-core series for this exact identity
- resolving evidence: Same-zip rows for every missing series at the exact config/effort identity, including a high-effort WeirdML cost suffix if Access is required
- umi_public: null

## near-miss-claude-sonnet-5-max

- affected model: `claude-sonnet-5-max`
- required identity: exact max configuration on all ten common-core series
- missing series: epoch-weirdml, weirdml-cost-per-run
- sources investigated: Epoch common-core members; Epoch weirdml_external.csv
- URLs investigated: https://epoch.ai/data/benchmark_data.zip; https://htihle.github.io/weirdml.html
- reason: Frozen Epoch extract is missing required common-core series for this exact identity
- resolving evidence: Same-zip rows for every missing series at the exact config/effort identity, including a high-effort WeirdML cost suffix if Access is required
- umi_public: null

## near-miss-claude-opus-4-8-max

- affected model: `claude-opus-4-8-max`
- required identity: exact max configuration on all ten common-core series
- missing series: epoch-weirdml, weirdml-cost-per-run
- sources investigated: Epoch common-core members; Epoch weirdml_external.csv
- URLs investigated: https://epoch.ai/data/benchmark_data.zip; https://htihle.github.io/weirdml.html
- reason: Frozen Epoch extract is missing required common-core series for this exact identity
- resolving evidence: Same-zip rows for every missing series at the exact config/effort identity, including a high-effort WeirdML cost suffix if Access is required
- umi_public: null

## series-deepswe-mean-cost

- affected model: `claude-fable-5-max`
- required identity: complete cost observation count
- missing series: deepswe-mean-cost
- sources investigated: DeepSWE reviewed facts; Epoch deepswe_external.csv
- URLs investigated: https://deepswe.datacurve.ai/; https://deepswe.datacurve.ai/artifacts/v1.1/trials.json; https://epoch.ai/data/benchmark_data.zip
- reason: Official DeepSWE v1.1 cost is observed on 432 of 436 scored Fable attempts and cannot enter a complete all-attempt Access series
- resolving evidence: Complete Fable cost denominator or another all-five billed/calculated series
- umi_public: null

## construct-context-reliability

- affected model: `edition-scope`
- required identity: exact Max or documented composite
- missing series: context_reliability_and_factual_discipline
- sources investigated: Epoch simpleqa_verified.csv (missing claude-fable-5_max); AA five-row extracts (anchor n=5)
- URLs investigated: https://epoch.ai/data/benchmark_data.zip; https://epoch.ai/benchmarks/about; https://artificialanalysis.ai/
- reason: No frozen public series has all five exact Max identities and an 8+ same-harness anchor panel for context reliability
- resolving evidence: A frozen same-harness extract with all five pilots plus 8+ anchors
- umi_public: null

## construct-language-instruction

- affected model: `edition-scope`
- required identity: exact Max or documented composite
- missing series: language_data_and_instruction_following
- sources investigated: Epoch live_bench_external.csv (zero 2026 Max pilots); AA five-row extracts (anchor n=5)
- URLs investigated: https://epoch.ai/data/benchmark_data.zip; https://livebench.ai/; https://artificialanalysis.ai/
- reason: No frozen public series has all five exact Max identities and an 8+ same-harness anchor panel for language, data, or instruction following
- resolving evidence: A frozen same-harness extract with all five pilots plus 8+ anchors
- umi_public: null

## construct-interactive-latency

- affected model: `edition-scope`
- required identity: exact Max or documented composite plus 8+ same-extract anchors
- missing series: interactive_service_responsiveness
- sources investigated: Epoch zip members with public latency or time-horizon columns; AA reviewed five-row facts
- URLs investigated: https://epoch.ai/data/benchmark_data.zip; https://artificialanalysis.ai/
- reason: No frozen public series has all five exact Max identities and an 8+ same-extract anchor panel for interactive service latency
- resolving evidence: A frozen same-harness latency extract with all five pilots plus 8+ anchors
- umi_public: null

## construct-billed-economics

- affected model: `edition-scope`
- required identity: verified deployment plus admissible billing record
- missing series: provider_billing_record
- sources investigated: Official five-card lab tariffs; DeepSWE LiteLLM dollars; AA calculated cost columns; CursorBench table averages; Epoch ARC cost-per-task metadata
- URLs investigated: https://deepswe.datacurve.ai/artifacts/v1.1/trials.json; https://artificialanalysis.ai/; https://cursor.com/cursorbench; https://epoch.ai/benchmarks/about
- reason: No frozen all-five 8+ billed ledger exists. Source-reported WeirdML cost is Access Economics, not observed provider billing
- resolving evidence: An admissible all-five billed task ledger with exact deployment identity
- umi_public: null

## construct-hierarchical-bootstrap

- affected model: `edition-scope`
- required identity: attempt-level residuals on the scored extracts
- missing series: attempt_level_residuals
- sources investigated: Epoch configuration-level means in the frozen zip; DeepSWE official trial ledger (facts-and-citations only)
- URLs investigated: https://epoch.ai/data/benchmark_data.zip; https://deepswe.datacurve.ai/artifacts/v1.1/trials.json
- reason: Frozen extracts are configuration-level means without attempt residuals, so hierarchical bootstrap remains unpublished
- resolving evidence: Redistributable attempt-level residuals for every headline series
- umi_public: null
