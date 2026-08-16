from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from scripts.run_openrouter_operational_pilot import (
    RUNNER_CONTRACT_VERSION,
    RunnerError,
    _billing_reconciliation,
    _decoded_object,
    _fingerprinted,
    _initialize_run,
    _read_fingerprinted,
    _write_bytes_new,
    _write_new,
)
from umi.controlled_eval import load_run_manifest, load_task_pack

ROOT = Path(__file__).parents[1]
PACK_PATH = ROOT / "data" / "operational" / "pilot-v0.1" / "mmlu-pro-test-balanced-70-v1.json"
MANIFEST_PATH = (
    ROOT / "data" / "operational" / "pilot-v0.1" / "openrouter-five-model-run.yaml"
)


def test_run_contract_is_immutable_and_resume_bound(tmp_path: Path) -> None:
    pack = load_task_pack(PACK_PATH)
    manifest = load_run_manifest(MANIFEST_PATH)
    assert manifest.harness_version == RUNNER_CONTRACT_VERSION
    output_dir = tmp_path / "controlled-run"
    _initialize_run(
        output_dir,
        "test-controlled-run-v1",
        date(2026, 8, 16),
        pack,
        manifest,
        resume=False,
    )
    _initialize_run(
        output_dir,
        "test-controlled-run-v1",
        date(2026, 8, 16),
        pack,
        manifest,
        resume=True,
    )
    with pytest.raises(RunnerError, match="does not match"):
        _initialize_run(
            output_dir,
            "different-run-v1",
            date(2026, 8, 16),
            pack,
            manifest,
            resume=True,
        )


def test_fingerprinted_artifact_rejects_tampering(tmp_path: Path) -> None:
    path = tmp_path / "credits.json"
    payload = _fingerprinted({"remaining_credits": 40.0})
    _write_new(path, payload)
    assert _read_fingerprinted(path) == payload

    altered = path.read_text(encoding="utf-8").replace("40.0", "41.0")
    path.write_text(altered, encoding="utf-8")
    with pytest.raises(RunnerError, match="fingerprint mismatch"):
        _read_fingerprinted(path)


def test_raw_body_writer_never_overwrites_and_decoder_fails_closed(tmp_path: Path) -> None:
    path = tmp_path / "response-body.json"
    _write_bytes_new(path, b'{"id":"generation-1"}')
    with pytest.raises(RunnerError, match="refusing to overwrite"):
        _write_bytes_new(path, b'{"id":"generation-2"}')
    assert _decoded_object(path.read_bytes(), "test://response") == {"id": "generation-1"}
    with pytest.raises(RunnerError, match="not valid JSON"):
        _decoded_object(b"not-json", "test://response")


def test_billing_promotion_requires_full_account_reconciliation() -> None:
    costs = [0.1, 0.2, 0.3]
    before = {"remaining_credits": 40.0}
    reconciled_after = {"remaining_credits": 39.4}
    total, delta, reconciled = _billing_reconciliation(costs, before, reconciled_after)
    assert total == pytest.approx(0.6)
    assert delta == pytest.approx(0.6)
    assert reconciled is True

    concurrent_usage_after = {"remaining_credits": 39.39}
    _, _, reconciled = _billing_reconciliation(costs, before, concurrent_usage_after)
    assert reconciled is False
