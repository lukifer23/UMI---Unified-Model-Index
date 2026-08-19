# UMI Public v0.6 verified source audit

v0.6 is a strict public-source audit for the five exact pilot configurations. It verifies what the frozen public evidence can support and withholds a headline Overall score.

- evidence cutoff: `2026-08-19T00:00:00Z`
- publication state: `verified_abstention`
- headline eligible: `false`
- source-audit fingerprint: `9c96c7be0c578294ee8e08c0aae72862d0e8ebd40d1c11cff79f06063aaa1ea7`

## Existing headline gates

| Gate | Observed | Required | Result |
|---|---:|---:|---|
| `capability` | 64.0% | 60.0% | pass |
| `economics` | 0.0% | 40.0% | **blocked** |
| `efficiency` | 4.5% | 50.0% | **blocked** |
| `overall` | 5.7% | 60.0% | **blocked** |

## Frozen-source admissibility

| Requirement | Sources | Result | Why |
|---|---|---|---|
| `common-core-capability` | `epoch-benchmark-data-2026-08-14` | pass | admitted |
| `rootcausebench-v3-final-trial-integrity` | `rootcausebench-v3-results-2026-08-16`, `rootcausebench-v3-config-2026-08-16`, `rootcausebench-v3-readme-2026-08-16`, `rootcausebench-v3-license-2026-08-16` | pass | admitted |
| `public-context-reliability` | `aa-omniscience-facts-2026-08-15` | **blocked** | aa-omniscience-facts-2026-08-15 is facts_only, requires full_artifact |
| `public-language-instruction` | none | **blocked** | no frozen public artifact is registered |
| `success-adjusted-efficiency` | `deepswe-v1.1-2026-08-13`, `aa-lcr-facts-2026-08-15` | **blocked** | deepswe-v1.1-2026-08-13 is facts_only, requires full_artifact; aa-lcr-facts-2026-08-15 is facts_only, requires full_artifact; no frozen exact-deployment evidence binding is available; attempt-level residuals are not redistributable in the admitted evidence |
| `interactive-latency` | `aa-lcr-facts-2026-08-15` | **blocked** | aa-lcr-facts-2026-08-15 is facts_only, requires full_artifact; no frozen exact-deployment evidence binding is available; attempt-level residuals are not redistributable in the admitted evidence |
| `provider-billed-economics` | none | **blocked** | no frozen public artifact is registered; no frozen exact-deployment evidence binding is available; attempt-level residuals are not redistributable in the admitted evidence |
| `hierarchical-bootstrap` | `epoch-benchmark-data-2026-08-14`, `deepswe-v1.1-2026-08-13` | **blocked** | deepswe-v1.1-2026-08-13 is facts_only, requires full_artifact; no frozen exact-deployment evidence binding is available; attempt-level residuals are not redistributable in the admitted evidence |

## Result

- `public-context-reliability`
- `public-language-instruction`
- `success-adjusted-efficiency`
- `interactive-latency`
- `provider-billed-economics`
- `hierarchical-bootstrap`

The audited v0.5 governed partial values remain provenance-bound historical inputs. They are not v0.6 Overall scores, and no missing requirement is imputed.
