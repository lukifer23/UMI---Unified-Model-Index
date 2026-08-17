# Public index surfaces

The interactive frontend is still deferred. The governed public index is the offline
v0.5 dashboard and certificate:

- `data/editions/v0.5/processed/public-dashboard.html`
- `data/editions/v0.5/processed/public-index-certificate.json`

Rebuild without scoring:

```bash
PYTHONPATH=. uv run --no-sync umi edition --edition v0.5 dashboard
PYTHONPATH=. uv run --no-sync umi edition --edition v0.5 certificate
```
