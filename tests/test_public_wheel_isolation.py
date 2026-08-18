from __future__ import annotations

from pathlib import Path

from umi.edition import edition_config_dir, load_public_edition_config
from umi.public import score_public_edition
from umi.public_paths import resolve_epoch_zip


def test_edition_config_is_found_from_checkout_or_package() -> None:
    directory = edition_config_dir("v0.5")
    assert (directory / "edition.yaml").is_file()
    config = load_public_edition_config(edition="v0.5")
    assert config.edition_id == "umi-public-v0.5"
    assert config.release_class == "provisional_public_score"


def test_score_from_tmp_cwd_with_explicit_bundle_dir(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    payload = score_public_edition(
        edition_name="v0.5",
        bundle_dir=resolve_epoch_zip().parent,
    )
    assert payload["certified"] is False
    assert payload["models"]
