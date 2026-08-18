# UMI Public v0.5 normalization

Edition: `umi-normalization-v0.5.0`. This does not rewrite v0.4 (`umi-normalization-v0.4.0`).

| Series kind | v0.4 | v0.5 |
|---|---|---|
| Bounded accuracy | logit, clip into (ε, 1-ε) | reject outside [0, 1], then logit |
| Cost / tokens / steps | `-log(x+1)` | `-log(x)`, require x > 0 |
| Robust scale | 1.4826 × MAD; IQR fallback `1.4826 × IQR / 1.349` | 1.4826 × MAD; IQR fallback `IQR / 1.349` |
| Duplicates | first seen | identical dedupe; conflict fails unless excluded |

Declared v0.5 exclusion: `Qwen3-235B-A22B-Thinking-2507` on WeirdML (two source row IDs,
different accuracy and cost).
