# Changelog

## 0.5.0 — UMI Public provisional

- Package version is `0.5.0`. v0.3 formula/engine identities in `umi.version` stay
  `umi-methodology-v0.3.15` / `umi-engine-v0.3.13` so legacy fingerprints do not move.
- v0.4 is frozen as `experimental_point_score`. Its five `umi_public` numbers are unchanged.
- v0.5 is `provisional_public_score`. It is not a certified headline.
- Production public scoring requires a `PublicScoringBundle` and an explicit Epoch zip path
  (`--bundle-dir`).
- Source concentration has no single-source exemption. CritPt is Artificial Analysis
  evaluator evidence distributed by Epoch.
- Effort is never inferred from `_max` / `_high` / `_xhigh` suffixes.
- v0.5 normalization uses `-log(x)` for cost/tokens and `IQR / 1.349` as the MAD fallback.
- Conflicting WeirdML row `Qwen3-235B-A22B-Thinking-2507` is excluded by declared policy.
- Strict ranks are not claimed. Live scores carry point order; interval ranks attach after
  uncertainty.
- `score_dataset` warns on ungoverned real data. Prefer `score_bundle` / `score_public_bundle`.
- Grok 4.5 High and Gemini 3.1 Pro Preview stay diagnostic (`insufficient_common_support`).

## 0.3.16

- Hosted operational runner hardening and v0.3.15 General Interaction workload authority.
  See `VERIFICATION.md`.
