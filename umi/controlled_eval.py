from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any

import yaml

from umi.schemas import (
    ControlledTask,
    ControlledTaskPack,
    OperationalDeploymentContract,
    OperationalRunManifest,
)


def canonical_fingerprint(payload: dict[str, Any]) -> str:
    value = dict(payload)
    value.pop("fingerprint", None)
    rendered = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(rendered.encode()).hexdigest()


def load_task_pack(path: str | Path) -> ControlledTaskPack:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    pack = ControlledTaskPack.model_validate(raw)
    if canonical_fingerprint(pack.model_dump(mode="json")) != pack.fingerprint:
        raise ValueError("controlled task pack fingerprint mismatch")
    return pack


def load_run_manifest(path: str | Path) -> OperationalRunManifest:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    manifest = OperationalRunManifest.model_validate(raw)
    if canonical_fingerprint(manifest.model_dump(mode="json")) != manifest.fingerprint:
        raise ValueError("operational run manifest fingerprint mismatch")
    return manifest


def validate_run_binding(
    pack: ControlledTaskPack, manifest: OperationalRunManifest
) -> tuple[str, ...]:
    errors: list[str] = []
    if canonical_fingerprint(pack.model_dump(mode="json")) != pack.fingerprint:
        errors.append("controlled task pack fingerprint mismatch")
    if canonical_fingerprint(manifest.model_dump(mode="json")) != manifest.fingerprint:
        errors.append("operational run manifest fingerprint mismatch")
    if manifest.task_pack_id != pack.pack_id:
        errors.append("run manifest task_pack_id does not match the task pack")
    if manifest.task_pack_fingerprint != pack.fingerprint:
        errors.append("run manifest task_pack_fingerprint does not match the task pack")
    return tuple(errors)


def task_prompt(task: ControlledTask) -> str:
    options = "\n".join(f"{chr(65 + index)}. {option}" for index, option in enumerate(task.options))
    return f"Question:\n{task.question}\n\nOptions:\n{options}"


SYSTEM_PROMPT = (
    "You are completing a controlled multiple-choice evaluation. Solve the problem "
    "independently. Return one JSON object with exactly one key, answer, whose value is the "
    "single uppercase option letter. Do not use external tools."
)


def request_payload(
    task: ControlledTask, deployment: OperationalDeploymentContract
) -> dict[str, Any]:
    endpoint = deployment.endpoint
    payload: dict[str, Any] = {
        "model": endpoint.router_model_id,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": task_prompt(task)},
        ],
        "max_tokens": endpoint.max_tokens,
        "reasoning": {"effort": endpoint.reasoning_effort.value, "exclude": True},
        "response_format": {"type": "json_object"},
        "provider": {
            "order": [endpoint.provider_slug],
            "allow_fallbacks": False,
            "require_parameters": True,
        },
        "stream": False,
    }
    if endpoint.service_tier_request is not None:
        payload["service_tier"] = endpoint.service_tier_request
    return payload


def maximum_request_cost_usd(
    task: ControlledTask, deployment: OperationalDeploymentContract
) -> float:
    """Conservative router-price ceiling; UTF-8 bytes bound prompt token count."""
    endpoint = deployment.endpoint
    prompt_bytes = len(SYSTEM_PROMPT.encode()) + len(task_prompt(task).encode())
    possible_cache_write_price = max(
        endpoint.cache_write_price_per_token_usd or 0,
        endpoint.cache_write_1h_price_per_token_usd or 0,
    )
    return (
        prompt_bytes
        * (endpoint.prompt_price_per_token_usd + possible_cache_write_price)
        + endpoint.max_tokens * endpoint.completion_price_per_token_usd
    )


def execution_schedule(
    pack: ControlledTaskPack, manifest: OperationalRunManifest
) -> tuple[tuple[ControlledTask, OperationalDeploymentContract], ...]:
    """Rotate deployment order per task so each occupies every ordinal equally."""
    deployments = manifest.deployments
    return tuple(
        (task, deployments[(task_index + offset) % len(deployments)])
        for task_index, task in enumerate(pack.tasks)
        for offset in range(len(deployments))
    )


def maximum_run_cost_usd(
    pack: ControlledTaskPack, manifest: OperationalRunManifest
) -> float:
    return sum(
        maximum_request_cost_usd(task, deployment)
        for deployment in manifest.deployments
        for task in pack.tasks
    )


def operational_preflight(
    pack: ControlledTaskPack, manifest: OperationalRunManifest
) -> dict[str, Any]:
    errors = validate_run_binding(pack, manifest)
    raw_per_deployment = {
        deployment.deployment_id: math.fsum(
            maximum_request_cost_usd(task, deployment) for task in pack.tasks
        )
        for deployment in manifest.deployments
    }
    per_deployment = {
        key: math.ceil(value * 1_000_000) / 1_000_000
        for key, value in raw_per_deployment.items()
    }
    return {
        "valid": not errors,
        "errors": errors,
        "task_pack_id": pack.pack_id,
        "task_pack_fingerprint": pack.fingerprint,
        "manifest_id": manifest.manifest_id,
        "manifest_fingerprint": manifest.fingerprint,
        "task_count": len(pack.tasks),
        "deployment_count": len(manifest.deployments),
        "request_count": len(pack.tasks) * len(manifest.deployments),
        "maximum_cost_usd": math.ceil(math.fsum(raw_per_deployment.values()) * 1_000_000)
        / 1_000_000,
        "maximum_cost_by_deployment_usd": per_deployment,
    }
