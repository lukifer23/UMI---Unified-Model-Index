# IMPLEMENTATION_REPORT_V05

## 1–4. Git identity

| Item | Value |
|---|---|
| Starting commit (feat tip) | `4af92006c1ec8263d693d7b03bca5c345b582729` |
| Reviewed spec baseline | `9712b35f2c3fe162110c4c29e25101f2fe3a58f8` |
| `origin/main` at start | `f4cc49b5ef3e79f60d15cbc302596c97eed078a2` |
| Branch | `feat/umi-v05-governed-public-2` |
| Ending commit | recorded at handoff in the status block |

Commits unique to this replacement branch:

1. `07ca9bd` Withhold certified v0.5 headlines and close source-cap and identity P0s
2. `77768d4` Add v0.4/v0.5 freeze checks, public API exports, and CI smokes
3. `c6edcc0` Score public editions only from a bundle, with v0.5 scales and no strict ranks
4. (this handoff) docs, wheel packaging, isolated public smoke, complete report

No reset, no force push, no history rewrite. Draft PR: https://github.com/lukifer23/UMI---Unified-Model-Index/pull/2

## 5. Baseline verification

v0.4 frozen scores (unchanged):

| Point order | Entity | Capability | OpEff | Access | UMI Public |
|---:|---|---:|---:|---:|---:|
| 1 | gpt-5.6-sol-max | 91.9448 | 49.6628 | 16.4025 | 66.2658 |
| 2 | kimi-k3-max | 88.8397 | 27.7968 | 19.3982 | 59.6907 |
| 3 | claude-opus-5-max | 90.7314 | 19.2591 | 3.9650 | 55.5100 |
| 4 | claude-fable-5-max | 88.7109 | 21.9899 | 0.7058 | 54.4296 |
| 5 | glm-5.2-max | 67.8856 | 23.2174 | 55.3063 | 54.2027 |

Fingerprint `e266af13b966cf79cfc5086513ec35f60cf2194f896f41f4b332f60ac9788e6d`.
Epoch zip `35a7c21ba7d535514ebcf9bbe7b8265d2e2da40ef6b1fa63fe49323c3395a18b`.

## 6. v0.4 classification

`experimental_point_score` / `historical_experimental_point_score`. Companion
`data/editions/v0.4/processed/release-status.json`. Ranks are point-estimate order only.

## 7. P0 dispositions

| ID | Disposition |
|---|---|
| P0-01 | Production score requires `PublicScoringBundle`. `--bundle-dir` locates the zip. |
| P0-02 | Series come from edition YAML. |
| P0-03 | `decide_public_eligibility` is shared; failed certification yields no headline. |
| P0-04 | No single-source exemption. CritPt origin is Artificial Analysis. |
| P0-05/06 | No suffix effort inference. Crosswalk is reviewed evidence. |
| P0-07 | Anchor members are explicit and fingerprinted. |
| P0-08/09 | v0.4 first-seen; v0.5 declared exclude for conflicting WeirdML Qwen row. |
| P0-10 | v0.5-only log / IQR/1.349 / range reject. v0.4 unchanged. |
| P0-11 | Hierarchy unchanged; missing parents do not silent-reweight certified construct. |
| P0-12/13/14 | Still unadjusted / single-source; labeled and certification withheld. |
| P0-15/16 | Partial source intervals; no strict ranks. |
| P0-17/18 | Bundle + certificate + sidecars. |
| P0-19 | Package 0.5.0; v0.3 formula ids unchanged; edition YAML holds public versions. |
| P0-20 | Packaged edition YAML in the wheel; zip via `--bundle-dir`. |
| P0-21 | `score` is read-only; `build` writes. Frozen v0.4 processed scores are not overwritten. |
| P0-22 | Edition score/build return 0 for successful provisional analysis. |
| P0-23 | `score_dataset` warns on ungoverned real data. |

## 8–18. Architecture and policy

See `docs/editions/v0.5/{PUBLICATION_POLICY,NORMALIZATION,LIMITATIONS,REPRODUCIBILITY}.md`
and `METHODOLOGY.md`. Formula remains 0.55 / 0.25 / 0.20. v0.5 target construct is in
`config/editions/v0.5/construct.yaml`. Experimental profile weights remain the 10-series basket.

## 19–21. Sources

Accepted for the experimental profile: the ten Epoch-zip series listed in
`config/editions/v0.5/common-core.yaml`. Rejected / diagnostic: DeepSWE incomplete Fable cost,
Grok/Gemini missing WeirdML cells, context/language/latency/billed Economics. Contamination:
Grok CursorBench stays diagnostic if ever admitted.

## 22–24. Candidates

- Grok 4.5 High: 8/10, missing WeirdML accuracy + cost, `insufficient_common_support`.
- Gemini 3.1 Pro Preview: 9/10, missing high-effort WeirdML cost, `insufficient_common_support`.
- Grok 4.6: intake only.

## 25–29. Scores

v0.4 frozen: see §5. Not recertified.

v0.5 experimental profile (new scale, provisional):

| Point order | Entity | UMI Public |
|---:|---|---:|
| 1 | gpt-5.6-sol-max | 68.2381 |
| 2 | kimi-k3-max | 61.4980 |
| 3 | claude-opus-5-max | 57.9330 |
| 4 | gpt-5.4-2026-03-05-xhigh | 57.8048 |
| 5 | claude-fable-5-max | 56.2826 |
| 6 | gemini-3.6-flash-high | 55.4022 |
| 7 | glm-5.2-max | 54.1857 |

No certified scores. Interval ranks attach on `build`. Places 2–7 overlap under partial intervals.

## 30–33. Sensitivity

Source ablation, weight sensitivity, and family ablation remain diagnostic JSON sidecars.
They do not change `umi_public`. External validation is not a weight-tuning target.

## 34–38. Verification

Executed at handoff (do not claim checks that were not run). See the status block.
No paid requests. No API keys.

## 39. Remaining blockers

- Access 1.00 WeirdML; OpEff 1.00 DataCurve
- Missing construct parents
- Success-adjusted resources unavailable on frozen extracts
- Hierarchical attempt bootstrap unpublished
- Grok 4.5 / Gemini 3.1 Pro common-core holes

## 40. Reproduction

See `docs/editions/v0.5/REPRODUCIBILITY.md`.
