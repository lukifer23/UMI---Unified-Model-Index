# UMI Public v0.5 reproducibility

Offline only. No API keys.

```bash
uv sync --frozen --extra dev --no-editable
PYTHONPATH=. uv run --no-sync pytest
PYTHONPATH=. uv run --no-sync ruff check .
PYTHONPATH=. uv run --no-sync mypy --strict umi analysis scripts
PYTHONPATH=. uv run --no-sync python -m scripts.generate_schemas
PYTHONPATH=. uv run --no-sync python -m scripts.build_v03_pilot
PYTHONPATH=. uv run --no-sync python -m scripts.build_v04_public --check
PYTHONPATH=. uv run --no-sync python -m scripts.build_v05_public --check
PYTHONPATH=. uv run --no-sync umi edition --edition v0.5 --bundle-dir data/sources/v0.3 score
```

Epoch zip SHA-256 must be
`35a7c21ba7d535514ebcf9bbe7b8265d2e2da40ef6b1fa63fe49323c3395a18b`.

v0.4 scored-data fingerprint:
`e266af13b966cf79cfc5086513ec35f60cf2194f896f41f4b332f60ac9788e6d`.

Installed wheel: pass `--bundle-dir` to the frozen zip. Edition YAML ships in the wheel
under `umi/packaged_config`.
