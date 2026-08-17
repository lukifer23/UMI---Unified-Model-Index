from __future__ import annotations

import json
import math
from datetime import date
from pathlib import Path
from typing import Any

import pytest

from scripts.run_openrouter_operational_pilot import (
    BILLING_RECONCILIATION_ABS_TOLERANCE_USD,
    REQUEST_ERROR_NAME,
    REVIEW_ERROR_NAME,
    RUNNER_CONTRACT_VERSION,
    RunnerError,
    _answer,
    _attempt_directory,
    _attempt_result,
    _billing_reconciliation,
    _canonical_bytes,
    _decoded_object,
    _finalize,
    _fingerprinted,
    _initialize_run,
    _ledger,
    _perform_attempt,
    _read_fingerprinted,
    _remaining_cost,
    _sha256_bytes,
    _status,
    _validate_generation,
    _write_bytes_new,
    _write_new,
    build_parser,
    inspect_run_status,
)
from umi.controlled_eval import (
    canonical_fingerprint,
    execution_schedule,
    load_run_manifest,
    load_task_pack,
    maximum_request_cost_usd,
    request_payload,
)
from umi.schemas import (
    ControlledTask,
    ControlledTaskPack,
    OperationalDeploymentContract,
    OperationalRunManifest,
)

ROOT = Path(__file__).parents[1]
PACK_PATH = ROOT / "data" / "operational" / "pilot-v0.1" / "mmlu-pro-test-balanced-70-v1.json"
MANIFEST_PATH = (
    ROOT / "data" / "operational" / "pilot-v0.1" / "openrouter-five-model-run.yaml"
)
OPERATIONAL_DATA = ROOT / "data" / "operational"
PILOT_DATA = ROOT / "data" / "pilots"


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


@pytest.fixture
def deny_http(monkeypatch: pytest.MonkeyPatch) -> None:
    def fail(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("HTTP must not be used in offline runner tests")

    monkeypatch.setattr("scripts.run_openrouter_operational_pilot._http_raw", fail)
    monkeypatch.setattr("scripts.run_openrouter_operational_pilot._http_json", fail)


@pytest.fixture(autouse=True)
def frozen_inputs_untouched() -> None:
    before = {path: path.read_bytes() for path in (PACK_PATH, MANIFEST_PATH)}
    yield
    assert {path: path.read_bytes() for path in (PACK_PATH, MANIFEST_PATH)} == before
    assert OPERATIONAL_DATA.is_dir()
    assert PILOT_DATA.is_dir()


def _cohort() -> tuple[
    ControlledTaskPack,
    OperationalRunManifest,
    ControlledTask,
    OperationalDeploymentContract,
]:
    pack = load_task_pack(PACK_PATH)
    manifest = load_run_manifest(MANIFEST_PATH)
    return pack, manifest, pack.tasks[0], manifest.deployments[0]


def _start_run(tmp_path: Path, pack: ControlledTaskPack, manifest: OperationalRunManifest) -> Path:
    output_dir = tmp_path / "controlled-run"
    _initialize_run(
        output_dir,
        "test-controlled-run-v1",
        date(2026, 8, 16),
        pack,
        manifest,
        resume=False,
    )
    return output_dir


def _synthetic_pack(tasks: tuple[ControlledTask, ...]) -> ControlledTaskPack:
    counts: dict[str, int] = {}
    for task in tasks:
        counts[task.category] = counts.get(task.category, 0) + 1
    per_category = next(iter(counts.values()))
    payload: dict[str, Any] = {
        "pack_version": "test-pack-v1",
        "pack_id": "test-offline-pack-v1",
        "source_dataset": "synthetic-offline",
        "source_revision": "a" * 40,
        "source_file": "synthetic-offline.json",
        "source_file_sha256": "b" * 64,
        "license_id": "mit",
        "config": "test",
        "split": "test",
        "selection_algorithm": "offline-test",
        "selection_seed": "offline-test",
        "tasks_per_category": per_category,
        "category_source_counts": counts,
        "category_selected_counts": counts,
        "tasks": [task.model_dump(mode="json") for task in tasks],
    }
    payload["fingerprint"] = canonical_fingerprint(payload)
    return ControlledTaskPack.model_validate(payload)


def _synthetic_manifest(
    pack: ControlledTaskPack,
    deployments: tuple[OperationalDeploymentContract, ...],
) -> OperationalRunManifest:
    payload = load_run_manifest(MANIFEST_PATH).model_dump(mode="json")
    payload["manifest_id"] = "test-offline-manifest-v1"
    payload["task_pack_id"] = pack.pack_id
    payload["task_pack_fingerprint"] = pack.fingerprint
    payload["deployments"] = [item.model_dump(mode="json") for item in deployments]
    payload["fingerprint"] = canonical_fingerprint(payload)
    return OperationalRunManifest.model_validate(payload)


def _response_generation_pair(
    task: ControlledTask,
    deployment: OperationalDeploymentContract,
    *,
    answer: str | None = None,
    content: str | None = None,
    response_model: str | None = None,
    generation_model: str | None = None,
    provider_name: str | None = None,
    service_tier: Any = "sentinel",
    response_cost: float = 0.01,
    generation_cost: float = 0.01,
    data_region: str | None = "us",
) -> tuple[dict[str, Any], dict[str, Any], bytes, bytes]:
    endpoint = deployment.endpoint
    if content is None:
        chosen = task.correct_answer if answer is None else answer
        content = json.dumps({"answer": chosen})
    response_body = {
        "id": "gen-1",
        "model": endpoint.router_model_id if response_model is None else response_model,
        "choices": [{"message": {"content": content}}],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 5,
            "cost": response_cost,
            "prompt_tokens_details": {"cached_tokens": 0, "cache_write_tokens": 0},
            "completion_tokens_details": {"reasoning_tokens": 1},
        },
    }
    generation_inner: dict[str, Any] = {
        "id": "gen-1",
        "model": (
            endpoint.canonical_snapshot_id if generation_model is None else generation_model
        ),
        "provider_name": endpoint.provider_name if provider_name is None else provider_name,
        "total_cost": generation_cost,
        "request_id": "req-1",
        "data_region": data_region,
        "upstream_id": "up-1",
    }
    if service_tier != "sentinel":
        generation_inner["service_tier"] = service_tier
    elif endpoint.expected_service_tier is not None:
        generation_inner["service_tier"] = endpoint.expected_service_tier
    raw_response = _canonical_bytes(response_body)
    raw_generation = _canonical_bytes({"data": generation_inner})
    request_bytes = _canonical_bytes(request_payload(task, deployment))
    response_artifact = {
        "request_sha256": _sha256_bytes(request_bytes),
        "wall_seconds": 1.25,
        "headers": {"content-type": "application/json"},
        "raw_body_path": "response-body.json",
        "body": response_body,
        "response_sha256": _sha256_bytes(raw_response),
    }
    generation_artifact = {
        "headers": {"content-type": "application/json"},
        "raw_body_path": "generation-body.json",
        "body": {"data": generation_inner},
        "generation_sha256": _sha256_bytes(raw_generation),
    }
    return response_artifact, generation_artifact, raw_response, raw_generation


def _write_retained_completion(
    output_dir: Path,
    task: ControlledTask,
    deployment: OperationalDeploymentContract,
    *,
    write_request: bool = True,
    raw_response: bytes | None = None,
    raw_generation: bytes | None = None,
    response_artifact: dict[str, Any] | None = None,
    generation_artifact: dict[str, Any] | None = None,
    **kwargs: Any,
) -> Path:
    directory = _attempt_directory(output_dir, task, deployment)
    if response_artifact is None or generation_artifact is None:
        built_response, built_generation, built_raw_response, built_raw_generation = (
            _response_generation_pair(task, deployment, **kwargs)
        )
        if response_artifact is None:
            response_artifact = built_response
        if generation_artifact is None:
            generation_artifact = built_generation
        if raw_response is None:
            raw_response = built_raw_response
        if raw_generation is None:
            raw_generation = built_raw_generation
    if write_request:
        _write_new(directory / "request.json", request_payload(task, deployment))
    _write_new(directory / "request-started.json", {"request_sha256": "started"})
    assert raw_response is not None
    assert raw_generation is not None
    _write_bytes_new(directory / "response-body.json", raw_response)
    _write_new(directory / "response.json", response_artifact)
    _write_bytes_new(directory / "generation-body.json", raw_generation)
    _write_new(directory / "generation.json", generation_artifact)
    return directory


def _perform(
    output_dir: Path,
    task: ControlledTask,
    deployment: OperationalDeploymentContract,
) -> dict[str, Any]:
    return _perform_attempt(
        output_dir,
        "https://openrouter.ai/api/v1",
        "unused-key",
        task,
        deployment,
    )


def _file_snapshot(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): _sha256_bytes(path.read_bytes())
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def test_perform_attempt_resumes_existing_result_without_http(
    tmp_path: Path, deny_http: None
) -> None:
    pack, manifest, task, deployment = _cohort()
    output_dir = _start_run(tmp_path, pack, manifest)
    response_artifact, generation_artifact, _, _ = _response_generation_pair(task, deployment)
    result = _attempt_result(task, deployment, response_artifact, generation_artifact)
    _write_new(_attempt_directory(output_dir, task, deployment) / "result.json", result)
    assert _perform(output_dir, task, deployment) == result


def test_perform_attempt_refuses_started_request_without_response(
    tmp_path: Path, deny_http: None
) -> None:
    pack, manifest, task, deployment = _cohort()
    output_dir = _start_run(tmp_path, pack, manifest)
    directory = _attempt_directory(output_dir, task, deployment)
    _write_new(directory / "request.json", request_payload(task, deployment))
    _write_new(directory / "request-started.json", {"request_sha256": "started"})
    with pytest.raises(RunnerError, match="refusing automatic retry"):
        _perform(output_dir, task, deployment)


def test_perform_attempt_refuses_existing_request_error(
    tmp_path: Path, deny_http: None
) -> None:
    pack, manifest, task, deployment = _cohort()
    output_dir = _start_run(tmp_path, pack, manifest)
    directory = _attempt_directory(output_dir, task, deployment)
    _write_new(
        directory / REQUEST_ERROR_NAME,
        {"error": "transport", "automatic_retry_permitted": False},
    )
    with pytest.raises(RunnerError, match="manual review"):
        _perform(output_dir, task, deployment)


def test_perform_attempt_rejects_request_bytes_drift(tmp_path: Path, deny_http: None) -> None:
    pack, manifest, task, deployment = _cohort()
    output_dir = _start_run(tmp_path, pack, manifest)
    directory = _attempt_directory(output_dir, task, deployment)
    drifted = request_payload(task, deployment)
    drifted["max_tokens"] = 1
    _write_new(directory / "request.json", drifted)
    with pytest.raises(RunnerError, match="stored request differs"):
        _perform(output_dir, task, deployment)


def test_perform_attempt_rejects_raw_body_checksum_mismatch(
    tmp_path: Path, deny_http: None
) -> None:
    pack, manifest, task, deployment = _cohort()
    output_dir = _start_run(tmp_path, pack, manifest)
    directory = _write_retained_completion(output_dir, task, deployment)
    original_response = (directory / "response-body.json").read_bytes()
    (directory / "response-body.json").write_bytes(b'{"tampered":true}')
    with pytest.raises(RunnerError, match="response raw-body checksum mismatch"):
        _perform(output_dir, task, deployment)
    (directory / "response-body.json").write_bytes(original_response)
    (directory / "generation-body.json").write_bytes(b'{"tampered":true}')
    with pytest.raises(RunnerError, match="generation raw-body checksum mismatch"):
        _perform(output_dir, task, deployment)


def test_answer_reject_modes_are_explicit() -> None:
    _, _, task, _ = _cohort()
    assert _answer({"choices": []}, task) == (None, "invalid_choice_count")
    assert _answer({"choices": [{"message": {}}]}, task) == (None, "missing_message_content")
    assert _answer(
        {"choices": [{"message": {"content": "not-json"}}]}, task
    ) == (None, "invalid_json_answer")
    assert _answer(
        {"choices": [{"message": {"content": json.dumps({"answer": "A", "extra": 1})}}]},
        task,
    ) == (None, "invalid_answer_object")
    assert _answer(
        {"choices": [{"message": {"content": json.dumps({"answer": "aa"})}}]},
        task,
    ) == (None, "invalid_answer_letter")
    out_of_range = chr(65 + len(task.options))
    letter, error = _answer(
        {"choices": [{"message": {"content": json.dumps({"answer": out_of_range})}}]},
        task,
    )
    assert letter == out_of_range
    assert error == "answer_out_of_range"


def test_validate_generation_rejects_identity_mismatches() -> None:
    _, _, task, deployment = _cohort()
    response_artifact, generation_artifact, _, _ = _response_generation_pair(
        task, deployment, response_model="other/model"
    )
    with pytest.raises(RunnerError, match="resolved deployment mismatch"):
        _validate_generation(
            response_artifact["body"], generation_artifact["body"]["data"], deployment
        )
    response_artifact, generation_artifact, _, _ = _response_generation_pair(
        task, deployment, provider_name="wrong-provider"
    )
    with pytest.raises(RunnerError, match="resolved deployment mismatch"):
        _validate_generation(
            response_artifact["body"], generation_artifact["body"]["data"], deployment
        )
    response_artifact, generation_artifact, _, _ = _response_generation_pair(
        task, deployment, service_tier="wrong-tier"
    )
    with pytest.raises(RunnerError, match="resolved deployment mismatch"):
        _validate_generation(
            response_artifact["body"], generation_artifact["body"]["data"], deployment
        )


def test_attempt_result_rejects_unreconciled_costs() -> None:
    _, _, task, deployment = _cohort()
    response_artifact, generation_artifact, _, _ = _response_generation_pair(
        task, deployment, response_cost=0.01, generation_cost=0.02
    )
    with pytest.raises(RunnerError, match="costs do not reconcile"):
        _attempt_result(task, deployment, response_artifact, generation_artifact)


def test_identity_and_cost_mismatches_persist_review_error_and_refuse_retry(
    tmp_path: Path, deny_http: None
) -> None:
    pack, manifest, task, deployment = _cohort()
    output_dir = _start_run(tmp_path, pack, manifest)
    _write_retained_completion(output_dir, task, deployment, response_model="other/model")
    directory = _attempt_directory(output_dir, task, deployment)
    with pytest.raises(RunnerError, match="resolved deployment mismatch"):
        _perform(output_dir, task, deployment)
    review = json.loads((directory / REVIEW_ERROR_NAME).read_text(encoding="utf-8"))
    assert review["automatic_retry_permitted"] is False
    with pytest.raises(RunnerError, match="manual review"):
        _perform(output_dir, task, deployment)

    second_dir = _start_run(tmp_path / "cost", pack, manifest)
    _write_retained_completion(
        second_dir, task, deployment, response_cost=0.01, generation_cost=0.02
    )
    with pytest.raises(RunnerError, match="costs do not reconcile"):
        _perform(second_dir, task, deployment)
    assert ( _attempt_directory(second_dir, task, deployment) / REVIEW_ERROR_NAME).is_file()


def test_remaining_cost_is_full_ceiling_until_response_exists(tmp_path: Path) -> None:
    pack, manifest, task, deployment = _cohort()
    output_dir = _start_run(tmp_path, pack, manifest)
    assert _remaining_cost(output_dir, pack, manifest) == pytest.approx(39.455197)
    directory = _attempt_directory(output_dir, task, deployment)
    _write_new(directory / "request.json", request_payload(task, deployment))
    assert _remaining_cost(output_dir, pack, manifest) == pytest.approx(39.455197)
    _write_new(directory / "response.json", {"placeholder": True})
    reduced = _remaining_cost(output_dir, pack, manifest)
    assert reduced < 39.455197
    remaining_raw = sum(
        maximum_request_cost_usd(item_task, item_deployment)
        for item_task, item_deployment in execution_schedule(pack, manifest)
        if not (
            item_task.task_id == task.task_id
            and item_deployment.deployment_id == deployment.deployment_id
        )
    )
    assert reduced == pytest.approx(math.ceil(remaining_raw * 1_000_000) / 1_000_000)


def test_status_reports_clean_mid_run_and_blocked_states(
    tmp_path: Path, deny_http: None, capsys: pytest.CaptureFixture[str]
) -> None:
    pack, manifest, task, deployment = _cohort()
    output_dir = _start_run(tmp_path, pack, manifest)
    before = _file_snapshot(output_dir)
    clean = inspect_run_status(output_dir, pack, manifest)
    assert clean["expected_attempts"] == 350
    assert clean["completed_attempts"] == 0
    assert clean["blocked_attempts"] == 0
    assert clean["remaining_attempts"] == 350
    assert clean["remaining_cost_usd"] == pytest.approx(39.455197)
    assert clean["finalize_possible"] is False
    assert "headline_overall" not in clean
    assert _file_snapshot(output_dir) == before

    response_artifact, generation_artifact, _, _ = _response_generation_pair(task, deployment)
    result = _attempt_result(task, deployment, response_artifact, generation_artifact)
    _write_retained_completion(output_dir, task, deployment)
    _write_new(_attempt_directory(output_dir, task, deployment) / "result.json", result)
    mid = inspect_run_status(output_dir, pack, manifest)
    assert mid["completed_attempts"] == 1
    assert mid["remaining_attempts"] == 349
    assert mid["remaining_cost_usd"] < 39.455197

    blocked_task = pack.tasks[1]
    blocked_deployment = manifest.deployments[0]
    blocked_dir = _attempt_directory(output_dir, blocked_task, blocked_deployment)
    _write_new(blocked_dir / "request-started.json", {"request_sha256": "started"})
    blocked = inspect_run_status(output_dir, pack, manifest)
    assert blocked["blocked_attempts"] == 1
    assert blocked["blocked"][0]["reasons"] == ["request_started_without_response"]
    assert blocked["finalize_possible"] is False

    args = build_parser().parse_args(
        [
            "--task-pack",
            str(PACK_PATH),
            "--run-manifest",
            str(MANIFEST_PATH),
            "--status",
            "--output-dir",
            str(output_dir),
        ]
    )
    assert args.accept_network is False
    assert _status(args) == 0
    rendered = json.loads(capsys.readouterr().out)
    assert rendered["blocked_attempts"] == 1
    assert rendered["completed_attempts"] == 1


def test_billing_reconciliation_tolerance_boundary() -> None:
    costs = [1.0]
    before = {"remaining_credits": 2.0}
    tolerance = BILLING_RECONCILIATION_ABS_TOLERANCE_USD
    at_tolerance = {"remaining_credits": 2.0 - (1.0 + tolerance)}
    beyond_tolerance = {"remaining_credits": 2.0 - (1.0 + (2 * tolerance))}
    _, _, reconciled_at = _billing_reconciliation(costs, before, at_tolerance)
    _, _, reconciled_beyond = _billing_reconciliation(costs, before, beyond_tolerance)
    assert reconciled_at is True
    assert reconciled_beyond is False


def test_finalize_refuses_incomplete_real_cohort(tmp_path: Path) -> None:
    pack, manifest, _, _ = _cohort()
    output_dir = _start_run(tmp_path, pack, manifest)
    with pytest.raises(RunnerError, match="0 of 350 completed results"):
        _finalize(
            output_dir,
            "test-controlled-run-v1",
            date(2026, 8, 16),
            pack,
            manifest,
            {"remaining_credits": 40.0},
            {"remaining_credits": 40.0},
        )


def test_ledger_rejects_missing_and_mixed_data_regions(tmp_path: Path) -> None:
    source_pack, _, _, deployment = _cohort()
    tasks = source_pack.tasks[:2]
    assert tasks[0].category == tasks[1].category
    pack = _synthetic_pack(tasks)
    manifest = _synthetic_manifest(pack, (deployment,))
    output_dir = _start_run(tmp_path, pack, manifest)
    _write_new(
        output_dir / "live-endpoint-preflight.json",
        _fingerprinted(
            {
                "manifest_fingerprint": manifest.fingerprint,
                "verified_deployments": [],
                "raw": {},
            }
        ),
    )
    _write_new(
        output_dir / "credits-before.json",
        _fingerprinted({"remaining_credits": 40.0, "total_credits": 40.0, "total_usage": 0.0}),
    )
    _write_new(
        output_dir / "credits-after.json",
        _fingerprinted({"remaining_credits": 39.0, "total_credits": 40.0, "total_usage": 1.0}),
    )

    def write_attempt(task: ControlledTask, region: str | None) -> None:
        directory = _attempt_directory(output_dir, task, deployment)
        for name in (
            "request-started.json",
            "request.json",
            "response.json",
            "generation.json",
        ):
            _write_new(directory / name, {"placeholder": name})
        _write_bytes_new(directory / "response-body.json", b"{}")
        _write_bytes_new(directory / "generation-body.json", b"{}")
        payload = {
            "task_id": task.task_id,
            "deployment_id": deployment.deployment_id,
            "attempt": {
                "task_id": task.task_id,
                "attempt_id": f"{deployment.deployment_id}-{task.task_id}-attempt-1",
                "success": True,
                "observed_cost_usd": 0.01,
                "billing_evidence": "router_response_cost",
                "cost_evidence_id": "gen-1",
                "data_region": region,
            },
        }
        _write_new(directory / "result.json", payload)

    write_attempt(tasks[0], None)
    write_attempt(tasks[1], "us")
    artifact_manifest = (
        output_dir / "deployments" / deployment.deployment_id / "raw-artifact-manifest.json"
    )
    with pytest.raises(RunnerError, match="missing or mixed data regions"):
        _ledger(
            output_dir,
            "test-controlled-run-v1",
            date(2026, 8, 16),
            deployment,
            pack,
            manifest,
            billing_reconciled=False,
        )
    artifact_manifest.unlink(missing_ok=True)

    for task in tasks:
        result_path = _attempt_directory(output_dir, task, deployment) / "result.json"
        payload = json.loads(result_path.read_text(encoding="utf-8"))
        payload["attempt"]["data_region"] = "us" if task is tasks[0] else "eu"
        result_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    with pytest.raises(RunnerError, match="missing or mixed data regions"):
        _ledger(
            output_dir,
            "test-controlled-run-v1",
            date(2026, 8, 16),
            deployment,
            pack,
            manifest,
            billing_reconciled=False,
        )


def test_status_and_helpers_do_not_claim_scoring_admission(tmp_path: Path) -> None:
    pack, manifest, _, _ = _cohort()
    output_dir = _start_run(tmp_path, pack, manifest)
    report = inspect_run_status(output_dir, pack, manifest)
    assert "headline_overall" not in report
    assert "scoring_admission" not in report
    assert report["finalize_possible"] is False
