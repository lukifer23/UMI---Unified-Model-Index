"""Locate frozen public source artifacts. Scoring must receive an explicit path."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
EPOCH_ZIP_NAME = "epoch-benchmark-data-2026-08-14.zip"
DEFAULT_EPOCH_ZIP = REPO_ROOT / "data" / "sources" / "v0.3" / EPOCH_ZIP_NAME


def resolve_epoch_zip(bundle_dir: Path | str | None = None) -> Path:
    if bundle_dir is None:
        if not DEFAULT_EPOCH_ZIP.is_file():
            raise FileNotFoundError(
                "Epoch zip not found; pass bundle_dir containing "
                f"{EPOCH_ZIP_NAME} or data/sources/v0.3/{EPOCH_ZIP_NAME}"
            )
        return DEFAULT_EPOCH_ZIP
    root = Path(bundle_dir)
    candidates = (
        root / EPOCH_ZIP_NAME,
        root / "sources" / "v0.3" / EPOCH_ZIP_NAME,
        root / "data" / "sources" / "v0.3" / EPOCH_ZIP_NAME,
        root / "v0.3" / EPOCH_ZIP_NAME,
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(
        f"Epoch zip {EPOCH_ZIP_NAME} not found under bundle-dir {root}"
    )
