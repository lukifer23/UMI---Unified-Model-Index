from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path

import pytest

from umi.cli import build_parser, run
from umi.controlled_eval import (
    load_run_manifest,
    load_task_pack,
    operational_preflight,
    request_payload,
)

ROOT = Path(__file__).parents[1]
PACK_PATH = ROOT / "data" / "operational" / "pilot-v0.1" / "mmlu-pro-test-balanced-70-v1.json"
MANIFEST_PATH = (
    ROOT / "data" / "operational" / "pilot-v0.1" / "openrouter-five-model-run.yaml"
)
SOURCE_PATH = ROOT / "data" / "sources" / "v0.4" / "mmlu-pro-test-b189ec765aa7.parquet"


def test_frozen_controlled_pack_is_source_bound_balanced_and_unique() -> None:
    pack = load_task_pack(PACK_PATH)
    assert hashlib.sha256(SOURCE_PATH.read_bytes()).hexdigest() == pack.source_file_sha256
    assert pack.source_revision == "b189ec765aa7ed75c8acfea42df31fdae71f97be"
    assert len(pack.tasks) == 70
    assert len(pack.category_selected_counts) == 14
    assert set(pack.category_selected_counts.values()) == {5}
    assert len({task.task_id for task in pack.tasks}) == 70
    assert all(task.correct_answer == chr(65 + task.correct_answer_index) for task in pack.tasks)


def test_operational_manifest_binds_all_five_exact_deployments_and_cost_ceiling() -> None:
    pack = load_task_pack(PACK_PATH)
    manifest = load_run_manifest(MANIFEST_PATH)
    report = operational_preflight(pack, manifest)
    assert report == {
        "valid": True,
        "errors": (),
        "task_pack_id": "mmlu-pro-test-balanced-70-v1",
        "task_pack_fingerprint": pack.fingerprint,
        "manifest_id": "openrouter-five-model-mmlu-pro-v1",
        "manifest_fingerprint": manifest.fingerprint,
        "task_count": 70,
        "deployment_count": 5,
        "request_count": 350,
        "maximum_cost_usd": 37.191602,
        "maximum_cost_by_deployment_usd": {
            "claude-opus-5-max-openrouter-anthropic-default": 7.48022,
            "claude-fable-5-max-openrouter-anthropic-default": 14.96044,
            "gpt-5.6-sol-max-openrouter-openai-default": 8.913821,
            "kimi-k3-max-openrouter-moonshot-mxfp4": 4.488132,
            "glm-5.2-max-openrouter-zai-fp8": 1.34899,
        },
    }
    mappings = {
        deployment.model_id: (
            deployment.endpoint.canonical_snapshot_id,
            deployment.endpoint.provider_slug,
            deployment.endpoint.reasoning_effort.value,
        )
        for deployment in manifest.deployments
    }
    assert mappings["glm-5.2-max"] == (
        "z-ai/glm-5.2-20260616",
        "z-ai/fp8",
        "xhigh",
    )
    assert {value[2] for key, value in mappings.items() if key != "glm-5.2-max"} == {"max"}


def test_request_is_fail_closed_and_never_sends_gold_answer() -> None:
    pack = load_task_pack(PACK_PATH)
    manifest = load_run_manifest(MANIFEST_PATH)
    task = pack.tasks[0]
    deployment = manifest.deployments[0]
    request = request_payload(task, deployment)
    assert request["model"] == deployment.endpoint.router_model_id
    assert request["provider"] == {
        "order": [deployment.endpoint.provider_slug],
        "allow_fallbacks": False,
        "require_parameters": True,
    }
    assert request["reasoning"] == {"effort": "max", "exclude": True}
    assert request["response_format"] == {"type": "json_object"}
    assert "service_tier" not in request
    serialized = json.dumps(request)
    assert "correct_answer" not in serialized
    assert "cot_content" not in serialized

    sol = next(item for item in manifest.deployments if item.model_id == "gpt-5.6-sol-max")
    assert request_payload(task, sol)["service_tier"] == "default"


def test_task_pack_and_manifest_fingerprints_fail_closed(tmp_path: Path) -> None:
    altered_pack = json.loads(PACK_PATH.read_text(encoding="utf-8"))
    altered_pack["tasks"][0]["question"] += " altered"
    pack_path = tmp_path / "pack.json"
    pack_path.write_text(json.dumps(altered_pack), encoding="utf-8")
    with pytest.raises(ValueError, match="fingerprint mismatch"):
        load_task_pack(pack_path)

    pack = load_task_pack(PACK_PATH)
    manifest = load_run_manifest(MANIFEST_PATH)
    changed = deepcopy(manifest.model_dump(mode="json"))
    changed["task_pack_fingerprint"] = "0" * 64
    changed["fingerprint"] = "0" * 64
    assert operational_preflight(pack, type(manifest).model_validate(changed))["valid"] is False


def test_operational_preflight_cli_is_offline(capsys: pytest.CaptureFixture[str]) -> None:
    args = build_parser().parse_args(
        [
            "operational",
            "preflight",
            "--task-pack",
            str(PACK_PATH),
            "--run-manifest",
            str(MANIFEST_PATH),
        ]
    )
    assert run(args) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["valid"] is True
    assert report["request_count"] == 350
