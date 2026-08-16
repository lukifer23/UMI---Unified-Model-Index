from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path
from typing import Any, cast

import yaml

from umi.attempt_ledger import aggregate_attempt_ledger
from umi.controlled_eval import (
    canonical_fingerprint,
    execution_schedule,
    load_run_manifest,
    load_task_pack,
    maximum_request_cost_usd,
    operational_preflight,
    request_payload,
)
from umi.schemas import (
    AttemptLedger,
    ControlledTask,
    ControlledTaskPack,
    OperationalDeploymentContract,
    OperationalRunManifest,
)

REQUIRED_ENDPOINT_PARAMETERS = {"max_tokens", "reasoning", "reasoning_effort", "response_format"}
SAFE_RESPONSE_HEADERS = {
    "content-type",
    "date",
    "openrouter-processing-time",
    "x-ratelimit-limit",
    "x-ratelimit-remaining",
    "x-ratelimit-reset",
    "x-request-id",
}
BILLING_RECONCILIATION_ABS_TOLERANCE_USD = 0.00000005
RUNNER_CONTRACT_VERSION = "umi-openrouter-controlled-harness-v0.2"


class RunnerError(ValueError):
    pass


def _canonical_bytes(payload: Any) -> bytes:
    return (
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
        )
        + "\n"
    ).encode()


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_new(path: Path, payload: Any) -> None:
    if path.exists() or path.with_name(path.name + ".tmp").exists():
        raise RunnerError(f"refusing to overwrite existing artifact: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_bytes(_canonical_bytes(payload))
    temporary.replace(path)


def _write_text_new(path: Path, value: str) -> None:
    if path.exists() or path.with_name(path.name + ".tmp").exists():
        raise RunnerError(f"refusing to overwrite existing artifact: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(value, encoding="utf-8")
    temporary.replace(path)


def _write_bytes_new(path: Path, value: bytes) -> None:
    if path.exists() or path.with_name(path.name + ".tmp").exists():
        raise RunnerError(f"refusing to overwrite existing artifact: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_bytes(value)
    temporary.replace(path)


def _read_json(path: Path) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise RunnerError(f"expected JSON object: {path}")
    return cast(dict[str, Any], raw)


def _fingerprinted(payload: dict[str, Any]) -> dict[str, Any]:
    value = dict(payload)
    value["fingerprint"] = canonical_fingerprint(value)
    return value


def _read_fingerprinted(path: Path) -> dict[str, Any]:
    payload = _read_json(path)
    if canonical_fingerprint(payload) != payload.get("fingerprint"):
        raise RunnerError(f"artifact fingerprint mismatch: {path}")
    return payload


def _headers(api_key: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/lukifer23/UMI---Unified-Model-Index",
        "X-Title": "UMI controlled operational pilot",
        "User-Agent": f"UMI-controlled-runner/0.3.14 ({RUNNER_CONTRACT_VERSION})",
    }


def _safe_headers(response: Any) -> dict[str, str]:
    return {
        key.lower(): value
        for key, value in response.headers.items()
        if key.lower() in SAFE_RESPONSE_HEADERS
    }


def _http_raw(
    method: str,
    url: str,
    api_key: str,
    payload: dict[str, Any] | None = None,
    *,
    timeout: float = 60,
) -> tuple[bytes, dict[str, str]]:
    body = _canonical_bytes(payload) if payload is not None else None
    request = urllib.request.Request(
        url,
        data=body,
        headers=_headers(api_key),
        method=method,
    )
    with urllib.request.urlopen(  # noqa: S310 - explicit network-and-cost-gated runner
        request, timeout=timeout
    ) as response:
        return response.read(), _safe_headers(response)


def _decoded_object(raw: bytes, url: str) -> dict[str, Any]:
    try:
        decoded = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise RunnerError(f"HTTP response was not valid JSON: {url}") from error
    if not isinstance(decoded, dict):
        raise RunnerError(f"HTTP response was not a JSON object: {url}")
    return cast(dict[str, Any], decoded)


def _http_json(
    method: str,
    url: str,
    api_key: str,
    payload: dict[str, Any] | None = None,
    *,
    timeout: float = 60,
) -> tuple[dict[str, Any], dict[str, str], bytes]:
    raw, headers = _http_raw(method, url, api_key, payload, timeout=timeout)
    return _decoded_object(raw, url), headers, raw


def _api_key(manifest: OperationalRunManifest) -> str:
    direct = os.environ.get("OPENROUTER_API_KEY")
    if direct:
        return direct
    compatible = os.environ.get("OPENAI_API_KEY")
    configured_base = os.environ.get("OPENAI_API_BASE", "")
    manifest_host = urllib.parse.urlparse(str(manifest.api_base_url)).netloc
    configured_host = urllib.parse.urlparse(configured_base).netloc
    if compatible and configured_host == manifest_host:
        return compatible
    raise RunnerError(
        "no compatible API key found; set OPENROUTER_API_KEY or pair OPENAI_API_KEY with "
        "an OPENAI_API_BASE matching the manifest host"
    )


def _selected_endpoint(
    raw: dict[str, Any], deployment: OperationalDeploymentContract
) -> dict[str, Any]:
    data = raw.get("data")
    if not isinstance(data, dict) or not isinstance(data.get("endpoints"), list):
        raise RunnerError("endpoint response lacks data.endpoints")
    matches = [
        item
        for item in data["endpoints"]
        if isinstance(item, dict) and item.get("tag") == deployment.endpoint.provider_slug
    ]
    if len(matches) != 1:
        raise RunnerError(
            f"expected one endpoint tagged {deployment.endpoint.provider_slug}; "
            f"found {len(matches)}"
        )
    return cast(dict[str, Any], matches[0])


def _validate_endpoint(
    models_raw: dict[str, Any],
    endpoints_raw: dict[str, Any],
    deployment: OperationalDeploymentContract,
) -> dict[str, Any]:
    models = models_raw.get("data")
    if not isinstance(models, list):
        raise RunnerError("model response lacks data list")
    matching_models = [
        item
        for item in models
        if isinstance(item, dict) and item.get("id") == deployment.endpoint.router_model_id
    ]
    if len(matching_models) != 1:
        raise RunnerError(
            f"router model identity is not unique: {deployment.endpoint.router_model_id}"
        )
    model = cast(dict[str, Any], matching_models[0])
    endpoint = _selected_endpoint(endpoints_raw, deployment)
    contract = deployment.endpoint
    expected: dict[str, Any] = {
        "canonical_slug": contract.canonical_snapshot_id,
        "endpoint_name": contract.endpoint_name,
        "provider_name": contract.provider_name,
        "context_length": contract.context_length,
        "max_completion_tokens": contract.max_completion_tokens_supported,
        "prompt_price": contract.prompt_price_per_token_usd,
        "completion_price": contract.completion_price_per_token_usd,
        "cache_read_price": contract.cache_read_price_per_token_usd,
        "cache_write_price": contract.cache_write_price_per_token_usd,
        "cache_write_1h_price": contract.cache_write_1h_price_per_token_usd,
    }
    pricing = endpoint.get("pricing")
    if not isinstance(pricing, dict):
        raise RunnerError(f"endpoint pricing is absent: {contract.provider_slug}")
    observed = {
        "canonical_slug": model.get("canonical_slug"),
        "endpoint_name": endpoint.get("name"),
        "provider_name": endpoint.get("provider_name"),
        "context_length": endpoint.get("context_length"),
        "max_completion_tokens": endpoint.get("max_completion_tokens"),
        "prompt_price": float(pricing["prompt"]),
        "completion_price": float(pricing["completion"]),
        "cache_read_price": (
            float(pricing["input_cache_read"])
            if pricing.get("input_cache_read") is not None
            else None
        ),
        "cache_write_price": (
            float(pricing["input_cache_write"])
            if pricing.get("input_cache_write") is not None
            else None
        ),
        "cache_write_1h_price": (
            float(pricing["input_cache_write_1h"])
            if pricing.get("input_cache_write_1h") is not None
            else None
        ),
    }
    mismatches = {
        key: {"expected": expected[key], "observed": observed[key]}
        for key in expected
        if expected[key] != observed[key]
    }
    supported = endpoint.get("supported_parameters")
    if not isinstance(supported, list):
        mismatches["supported_parameters"] = {
            "expected": sorted(REQUIRED_ENDPOINT_PARAMETERS),
            "observed": supported,
        }
    else:
        missing = REQUIRED_ENDPOINT_PARAMETERS - {str(item) for item in supported}
        if missing:
            mismatches["supported_parameters"] = {
                "expected": sorted(REQUIRED_ENDPOINT_PARAMETERS),
                "observed_missing": sorted(missing),
            }
    reasoning = model.get("reasoning")
    efforts = reasoning.get("supported_efforts") if isinstance(reasoning, dict) else None
    if not isinstance(efforts, list) or contract.reasoning_effort.value not in efforts:
        mismatches["reasoning_effort"] = {
            "expected": contract.reasoning_effort.value,
            "observed_supported": efforts,
        }
    if mismatches:
        raise RunnerError(
            f"live endpoint contract mismatch for {deployment.deployment_id}: "
            + json.dumps(mismatches, sort_keys=True)
        )
    return {
        "deployment_id": deployment.deployment_id,
        "model_id": deployment.model_id,
        "router_model_id": contract.router_model_id,
        "canonical_snapshot_id": contract.canonical_snapshot_id,
        "provider_slug": contract.provider_slug,
        "provider_name": contract.provider_name,
        "reasoning_effort": contract.reasoning_effort.value,
        "service_tier_request": contract.service_tier_request,
        "expected_service_tier": contract.expected_service_tier,
        "prices_verified": True,
        "parameters_verified": True,
    }


def _credits(api_base: str, api_key: str) -> dict[str, Any]:
    raw, _, _ = _http_json("GET", f"{api_base}/credits", api_key)
    data = raw.get("data")
    if not isinstance(data, dict):
        raise RunnerError("credits response lacks data object")
    total_credits = float(data["total_credits"])
    total_usage = float(data["total_usage"])
    return {
        "total_credits": total_credits,
        "total_usage": total_usage,
        "remaining_credits": total_credits - total_usage,
    }


def _live_preflight(
    pack: ControlledTaskPack,
    manifest: OperationalRunManifest,
    api_key: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    api_base = str(manifest.api_base_url).rstrip("/")
    models_raw, _, _ = _http_json("GET", f"{api_base}/models", api_key)
    verified = []
    selected_raw_models: dict[str, Any] = {}
    selected_raw_endpoints: dict[str, Any] = {}
    for deployment in manifest.deployments:
        model_path = urllib.parse.quote(deployment.endpoint.router_model_id, safe="/")
        endpoints_raw, _, _ = _http_json(
            "GET", f"{api_base}/models/{model_path}/endpoints", api_key
        )
        verified.append(_validate_endpoint(models_raw, endpoints_raw, deployment))
        models = cast(list[Any], models_raw["data"])
        selected_raw_models[deployment.deployment_id] = next(
            item
            for item in models
            if isinstance(item, dict)
            and item.get("id") == deployment.endpoint.router_model_id
        )
        selected_raw_endpoints[deployment.deployment_id] = _selected_endpoint(
            endpoints_raw, deployment
        )
    credits = _credits(api_base, api_key)
    offline = operational_preflight(pack, manifest)
    report = {
        **offline,
        "live_endpoint_contracts_valid": True,
        "verified_deployments": verified,
        "credits": credits,
        "funded_for_full_ceiling": credits["remaining_credits"] >= offline["maximum_cost_usd"],
    }
    raw = {"models": selected_raw_models, "endpoints": selected_raw_endpoints}
    return report, raw


def _attempt_directory(
    output_dir: Path, task: ControlledTask, deployment: OperationalDeploymentContract
) -> Path:
    return output_dir / "deployments" / deployment.deployment_id / "attempts" / task.task_id


def _response_body(response_artifact: dict[str, Any]) -> dict[str, Any]:
    body = response_artifact.get("body")
    if not isinstance(body, dict):
        raise RunnerError("response artifact lacks body object")
    return cast(dict[str, Any], body)


def _generation_data(generation_artifact: dict[str, Any]) -> dict[str, Any]:
    body = generation_artifact.get("body")
    data = body.get("data") if isinstance(body, dict) else None
    if not isinstance(data, dict):
        raise RunnerError("generation artifact lacks body.data object")
    return cast(dict[str, Any], data)


def _fetch_generation(
    api_base: str, api_key: str, generation_id: str
) -> tuple[dict[str, Any], dict[str, str], bytes]:
    url = f"{api_base}/generation?{urllib.parse.urlencode({'id': generation_id})}"
    last_error: Exception | None = None
    for delay in (0, 1, 2, 4, 8):
        if delay:
            time.sleep(delay)
        try:
            return _http_json("GET", url, api_key)
        except urllib.error.HTTPError as error:
            last_error = error
            if error.code != 404:
                raise
    raise RunnerError(f"generation metadata not available for {generation_id}: {last_error}")


def _validate_generation(
    response: dict[str, Any],
    generation: dict[str, Any],
    deployment: OperationalDeploymentContract,
) -> None:
    endpoint = deployment.endpoint
    mismatches: dict[str, Any] = {}
    response_model = response.get("model")
    if response_model not in {endpoint.router_model_id, endpoint.canonical_snapshot_id}:
        mismatches["response_model"] = response_model
    for key, expected in (
        ("model", endpoint.canonical_snapshot_id),
        ("provider_name", endpoint.provider_name),
        ("service_tier", endpoint.expected_service_tier),
    ):
        if generation.get(key) != expected:
            mismatches[key] = {"expected": expected, "observed": generation.get(key)}
    if mismatches:
        raise RunnerError(
            f"resolved deployment mismatch for {deployment.deployment_id}: "
            + json.dumps(mismatches, sort_keys=True)
        )


def _answer(response: dict[str, Any], task: ControlledTask) -> tuple[str | None, str | None]:
    choices = response.get("choices")
    if not isinstance(choices, list) or len(choices) != 1 or not isinstance(choices[0], dict):
        return None, "invalid_choice_count"
    message = choices[0].get("message")
    content = message.get("content") if isinstance(message, dict) else None
    if not isinstance(content, str):
        return None, "missing_message_content"
    try:
        decoded = json.loads(content)
    except json.JSONDecodeError:
        return None, "invalid_json_answer"
    if not isinstance(decoded, dict) or set(decoded) != {"answer"}:
        return None, "invalid_answer_object"
    answer = decoded.get("answer")
    if not isinstance(answer, str) or len(answer) != 1 or not answer.isupper():
        return None, "invalid_answer_letter"
    if ord(answer) - 65 >= len(task.options):
        return answer, "answer_out_of_range"
    return answer, None


def _integer_or_none(value: Any) -> int | None:
    return int(value) if isinstance(value, int | float) and value >= 0 else None


def _attempt_result(
    task: ControlledTask,
    deployment: OperationalDeploymentContract,
    response_artifact: dict[str, Any],
    generation_artifact: dict[str, Any],
) -> dict[str, Any]:
    response = _response_body(response_artifact)
    generation = _generation_data(generation_artifact)
    _validate_generation(response, generation, deployment)
    answer, answer_error = _answer(response, task)
    usage = response.get("usage")
    if not isinstance(usage, dict):
        raise RunnerError("response lacks usage accounting")
    prompt_details = usage.get("prompt_tokens_details")
    completion_details = usage.get("completion_tokens_details")
    prompt_details = prompt_details if isinstance(prompt_details, dict) else {}
    completion_details = completion_details if isinstance(completion_details, dict) else {}
    completion_tokens = _integer_or_none(usage.get("completion_tokens"))
    reasoning_tokens = _integer_or_none(completion_details.get("reasoning_tokens"))
    visible_output_tokens = (
        completion_tokens - reasoning_tokens
        if completion_tokens is not None
        and reasoning_tokens is not None
        and completion_tokens >= reasoning_tokens
        else None
    )
    response_cost = usage.get("cost")
    generation_cost = generation.get("total_cost")
    if not isinstance(response_cost, int | float) or not isinstance(
        generation_cost, int | float
    ):
        raise RunnerError("response/generation cost accounting is incomplete")
    if not math.isclose(float(response_cost), float(generation_cost), abs_tol=1e-12):
        raise RunnerError("response and generation costs do not reconcile")
    success = answer_error is None and answer == task.correct_answer
    error_kind = answer_error or (None if success else "incorrect_answer")
    attempt = {
        "task_id": task.task_id,
        "attempt_id": f"{deployment.deployment_id}-{task.task_id}-attempt-1",
        "success": success,
        "input_tokens": _integer_or_none(usage.get("prompt_tokens")),
        "output_tokens": visible_output_tokens,
        "reasoning_tokens": reasoning_tokens,
        "cache_read_tokens": _integer_or_none(prompt_details.get("cached_tokens")),
        "cache_write_tokens": _integer_or_none(prompt_details.get("cache_write_tokens")),
        "turns": 1,
        "agent_steps": 1,
        "wall_seconds": float(response_artifact["wall_seconds"]),
        "tool_calls": 0,
        "retry_count": 0,
        "observed_cost_usd": float(generation_cost),
        "billing_evidence": "router_response_cost",
        "cost_evidence_id": str(generation["id"]),
        "provider_request_id": (
            str(generation["request_id"]) if generation.get("request_id") else None
        ),
        "generation_id": str(generation["id"]),
        "resolved_model_id": str(generation["model"]),
        "serving_provider": str(generation["provider_name"]),
        "service_tier": generation.get("service_tier"),
        "data_region": generation.get("data_region"),
        "upstream_id": generation.get("upstream_id"),
        "error_kind": error_kind,
    }
    result: dict[str, Any] = {
        "task_id": task.task_id,
        "deployment_id": deployment.deployment_id,
        "returned_answer": answer,
        "correct_answer": task.correct_answer,
        "answer_error": answer_error,
        "success": success,
        "request_sha256": str(response_artifact["request_sha256"]),
        "response_sha256": str(response_artifact["response_sha256"]),
        "generation_sha256": str(generation_artifact["generation_sha256"]),
        "attempt": attempt,
    }
    result["fingerprint"] = canonical_fingerprint(result)
    return result


def _perform_attempt(
    output_dir: Path,
    api_base: str,
    api_key: str,
    task: ControlledTask,
    deployment: OperationalDeploymentContract,
) -> dict[str, Any]:
    directory = _attempt_directory(output_dir, task, deployment)
    request_path = directory / "request.json"
    started_path = directory / "request-started.json"
    response_body_path = directory / "response-body.json"
    response_path = directory / "response.json"
    generation_body_path = directory / "generation-body.json"
    generation_path = directory / "generation.json"
    result_path = directory / "result.json"
    error_path = directory / "request-error.json"
    error_body_path = directory / "request-error-body.bin"
    if result_path.is_file():
        result = _read_json(result_path)
        if canonical_fingerprint(result) != result.get("fingerprint"):
            raise RunnerError(f"attempt result fingerprint mismatch: {result_path}")
        return result
    if error_path.exists():
        raise RunnerError(f"ambiguous or failed paid request requires manual review: {error_path}")
    request = request_payload(task, deployment)
    request_bytes = _canonical_bytes(request)
    request_sha256 = _sha256_bytes(request_bytes)
    if request_path.exists() and request_path.read_bytes() != request_bytes:
        raise RunnerError(f"stored request differs from the current contract: {request_path}")
    if not response_path.exists():
        if started_path.exists():
            raise RunnerError(
                "paid request started without a retained response; refusing automatic retry: "
                f"{started_path}"
            )
        if not request_path.exists():
            _write_new(request_path, request)
        _write_new(
            started_path,
            {
                "request_sha256": request_sha256,
                "note": "Written immediately before the one authorized paid HTTP request",
            },
        )
        started = time.perf_counter()
        try:
            raw_response, response_headers = _http_raw(
                "POST", f"{api_base}/chat/completions", api_key, request, timeout=600
            )
        except Exception as error:
            error_details: dict[str, Any] = {
                "error_type": type(error).__name__,
                "error": str(error),
                "request_sha256": request_sha256,
                "automatic_retry_permitted": False,
            }
            if isinstance(error, urllib.error.HTTPError):
                raw_error_body = error.read()
                _write_bytes_new(error_body_path, raw_error_body)
                error_details.update(
                    {
                        "http_status": error.code,
                        "headers": _safe_headers(error),
                        "raw_body_path": error_body_path.name,
                        "raw_body_sha256": _sha256_bytes(raw_error_body),
                    }
                )
            _write_new(
                error_path,
                error_details,
            )
            raise
        wall_seconds = time.perf_counter() - started
        _write_bytes_new(response_body_path, raw_response)
        response_sha256 = _sha256_bytes(raw_response)
        try:
            response = _decoded_object(raw_response, f"{api_base}/chat/completions")
        except RunnerError as error:
            _write_new(
                error_path,
                {
                    "error_type": type(error).__name__,
                    "error": str(error),
                    "request_sha256": request_sha256,
                    "response_sha256": response_sha256,
                    "response_body_path": response_body_path.name,
                    "automatic_retry_permitted": False,
                },
            )
            raise
        response_payload: dict[str, Any] = {
            "request_sha256": request_sha256,
            "wall_seconds": wall_seconds,
            "headers": response_headers,
            "raw_body_path": response_body_path.name,
            "body": response,
        }
        response_payload["response_sha256"] = response_sha256
        _write_new(response_path, response_payload)
    response_artifact = _read_json(response_path)
    if response_artifact.get("request_sha256") != request_sha256:
        raise RunnerError(f"response is not bound to the stored request: {response_path}")
    response_checksum = response_artifact.get("response_sha256")
    if (
        not response_body_path.is_file()
        or _sha256_file(response_body_path) != response_checksum
    ):
        raise RunnerError(f"response raw-body checksum mismatch: {response_body_path}")
    response = _response_body(response_artifact)
    generation_id = response.get("id")
    if not isinstance(generation_id, str) or not generation_id:
        raise RunnerError("completion response lacks a generation ID")
    if not generation_path.exists():
        generation, generation_headers, raw_generation = _fetch_generation(
            api_base, api_key, generation_id
        )
        _write_bytes_new(generation_body_path, raw_generation)
        generation_payload: dict[str, Any] = {
            "headers": generation_headers,
            "raw_body_path": generation_body_path.name,
            "body": generation,
        }
        generation_payload["generation_sha256"] = _sha256_bytes(raw_generation)
        _write_new(generation_path, generation_payload)
    generation_artifact = _read_json(generation_path)
    if not generation_body_path.is_file() or _sha256_file(
        generation_body_path
    ) != generation_artifact.get("generation_sha256"):
        raise RunnerError(f"generation raw-body checksum mismatch: {generation_body_path}")
    result = _attempt_result(task, deployment, response_artifact, generation_artifact)
    _write_new(result_path, result)
    return result


def _initialize_run(
    output_dir: Path,
    run_id: str,
    evaluation_date: date,
    pack: ControlledTaskPack,
    manifest: OperationalRunManifest,
    *,
    resume: bool,
) -> None:
    if re.fullmatch(r"[a-z0-9][a-z0-9._-]*", run_id) is None:
        raise RunnerError("run ID must be a lowercase UMI identifier")
    state_path = output_dir / "run-contract.json"
    expected = {
        "run_state_version": "umi-openrouter-run-state-v0.2",
        "runner_contract_version": RUNNER_CONTRACT_VERSION,
        "runner_source_sha256": _sha256_file(Path(__file__)),
        "run_id": run_id,
        "evaluation_date": evaluation_date.isoformat(),
        "task_pack_id": pack.pack_id,
        "task_pack_fingerprint": pack.fingerprint,
        "manifest_id": manifest.manifest_id,
        "manifest_fingerprint": manifest.fingerprint,
    }
    expected["fingerprint"] = canonical_fingerprint(expected)
    if output_dir.exists():
        if not resume:
            raise RunnerError("output directory exists; --resume is required")
        if not state_path.is_file() or _read_json(state_path) != expected:
            raise RunnerError("existing output directory does not match the requested run contract")
        return
    if resume:
        raise RunnerError("--resume was supplied but the output directory does not exist")
    output_dir.mkdir(parents=True, exist_ok=False)
    _write_new(state_path, expected)


def _artifact_manifest(
    output_dir: Path,
    run_id: str,
    deployment: OperationalDeploymentContract,
    pack: ControlledTaskPack,
    manifest: OperationalRunManifest,
) -> tuple[dict[str, Any], Path]:
    deployment_root = output_dir / "deployments" / deployment.deployment_id
    result_paths = sorted(deployment_root.glob("attempts/*/result.json"))
    if len(result_paths) != len(pack.tasks):
        raise RunnerError(
            f"deployment {deployment.deployment_id} has {len(result_paths)} of "
            f"{len(pack.tasks)} results"
        )
    included: list[dict[str, Any]] = []
    for name in (
        "run-contract.json",
        "live-endpoint-preflight.json",
        "credits-before.json",
        "credits-after.json",
    ):
        path = output_dir / name
        if not path.is_file():
            raise RunnerError(f"complete run is missing {path}")
        included.append(
            {
                "path": name,
                "sha256": _sha256_file(path),
                "size_bytes": path.stat().st_size,
            }
        )
    for result_path in result_paths:
        attempt_root = result_path.parent
        for name in (
            "request-started.json",
            "request.json",
            "response-body.json",
            "response.json",
            "generation-body.json",
            "generation.json",
            "result.json",
        ):
            path = attempt_root / name
            if not path.is_file():
                raise RunnerError(f"complete attempt is missing {path}")
            included.append(
                {
                    "path": str(path.relative_to(output_dir)),
                    "sha256": _sha256_file(path),
                    "size_bytes": path.stat().st_size,
                }
            )
    payload: dict[str, Any] = {
        "artifact_manifest_version": "umi-raw-attempt-artifact-v0.1",
        "source_artifact_id": f"{run_id}-{deployment.deployment_id}-raw",
        "run_id": run_id,
        "deployment_id": deployment.deployment_id,
        "task_pack_fingerprint": pack.fingerprint,
        "run_manifest_fingerprint": manifest.fingerprint,
        "files": included,
    }
    payload["fingerprint"] = canonical_fingerprint(payload)
    path = deployment_root / "raw-artifact-manifest.json"
    if path.exists():
        if _read_json(path) != payload:
            raise RunnerError(f"raw artifact manifest drift: {path}")
    else:
        _write_new(path, payload)
    return payload, path


def _ledger(
    output_dir: Path,
    run_id: str,
    evaluation_date: date,
    deployment: OperationalDeploymentContract,
    pack: ControlledTaskPack,
    manifest: OperationalRunManifest,
    *,
    billing_reconciled: bool,
) -> AttemptLedger:
    artifact, artifact_path = _artifact_manifest(
        output_dir, run_id, deployment, pack, manifest
    )
    result_paths = sorted(
        (output_dir / "deployments" / deployment.deployment_id).glob("attempts/*/result.json")
    )
    attempts = [dict(_read_json(path)["attempt"]) for path in result_paths]
    if billing_reconciled:
        for attempt in attempts:
            attempt["billing_evidence"] = "provider_billing_record"
    endpoint = deployment.endpoint
    regions = {item.get("data_region") for item in attempts}
    if None in regions or len(regions) != 1:
        raise RunnerError(
            f"deployment {deployment.deployment_id} has missing or mixed data regions: "
            f"{sorted(str(item) for item in regions)}"
        )
    payload = {
        "ledger_id": f"{run_id}-{deployment.model_id}",
        "source": {
            "organization": "OpenRouter",
            "url": "https://openrouter.ai/api/v1/generation",
            "accessed": evaluation_date.isoformat(),
        },
        "source_artifact_id": artifact["source_artifact_id"],
        "source_artifact_sha256": _sha256_file(artifact_path),
        "crosswalk_entry_id": deployment.crosswalk_entry_id,
        "capture_type": "raw_upstream_payload",
        "redistribution_scope": "full_artifact",
        "model_release_date": deployment.model_release_date.isoformat(),
        "measurement_as_of_date": evaluation_date.isoformat(),
        "deployment": {
            "id": deployment.deployment_id,
            "model_id": deployment.model_id,
            "configuration": deployment.canonical_configuration.value,
            "named_release": deployment.named_release,
            "source_model_id": endpoint.canonical_snapshot_id,
            "serving_provider": endpoint.provider_name,
            "endpoint_id": endpoint.canonical_snapshot_id,
            "service_tier": endpoint.expected_service_tier or "not_applicable",
            "provider_snapshot_id": endpoint.canonical_snapshot_id,
            "region": next(iter(regions)),
            "configuration_verification": {
                "model_label_exact": True,
                "release_label_exact": True,
                "effort_label_exact": True,
                "fallback_absent": True,
                "provider_snapshot_verified": True,
                "endpoint_verified": True,
                "service_tier_verified": True,
                "deployment_identity_verified": True,
            },
        },
        "workload": manifest.workload,
        "workload_category": manifest.workload_category.value,
        "interaction_profile": manifest.interaction_profile.value,
        "operational_profile_id": manifest.operational_profile_id,
        "cohort_key": manifest.cohort_key,
        "evaluation_date": evaluation_date.isoformat(),
        "workload_version": manifest.workload_version,
        "harness_version": manifest.harness_version,
        "harness_owner": "UMI",
        "run_executor": "UMI open-source controlled runner",
        "evaluator": "UMI exact-option deterministic grader",
        "success_definition_id": manifest.success_definition_id,
        "success_definition": manifest.success_definition,
        "tools_enabled": manifest.tools_enabled,
        "signal_id": "mmlu-pro-controlled-general-resources-v1",
        "record_status": "ready",
        "scoring_disposition": "scored",
        "attempts": attempts,
    }
    return AttemptLedger.model_validate(payload)


def _finalize(
    output_dir: Path,
    run_id: str,
    evaluation_date: date,
    pack: ControlledTaskPack,
    manifest: OperationalRunManifest,
    credits_before: dict[str, Any],
    credits_after: dict[str, Any],
) -> dict[str, Any]:
    all_result_paths = sorted(output_dir.glob("deployments/*/attempts/*/result.json"))
    expected_results = len(pack.tasks) * len(manifest.deployments)
    if len(all_result_paths) != expected_results:
        raise RunnerError(
            f"run has {len(all_result_paths)} of {expected_results} completed results"
        )
    result_costs = [
        float(_read_json(path)["attempt"]["observed_cost_usd"])
        for path in all_result_paths
    ]
    total_cost, credit_delta, billing_reconciled = _billing_reconciliation(
        result_costs, credits_before, credits_after
    )
    summaries = []
    summarized_cost = 0.0
    for deployment in manifest.deployments:
        ledger = _ledger(
            output_dir,
            run_id,
            evaluation_date,
            deployment,
            pack,
            manifest,
            billing_reconciled=billing_reconciled,
        )
        aggregation = aggregate_attempt_ledger(ledger)
        ledger_path = output_dir / "ledgers" / f"{deployment.deployment_id}.yaml"
        ledger_text = yaml.safe_dump(ledger.model_dump(mode="json"), sort_keys=False)
        if ledger_path.exists():
            if ledger_path.read_text(encoding="utf-8") != ledger_text:
                raise RunnerError(f"ledger drift: {ledger_path}")
        else:
            ledger_path.parent.mkdir(parents=True, exist_ok=True)
            _write_text_new(ledger_path, ledger_text)
        aggregation_payload = aggregation.model_dump(mode="json")
        aggregation_path = output_dir / "aggregations" / f"{deployment.deployment_id}.json"
        if aggregation_path.exists():
            if _read_json(aggregation_path) != aggregation_payload:
                raise RunnerError(f"aggregation drift: {aggregation_path}")
        else:
            _write_new(aggregation_path, aggregation_payload)
        deployment_cost = math.fsum(
            float(item.observed_cost_usd or 0) for item in ledger.attempts
        )
        summarized_cost = math.fsum((summarized_cost, deployment_cost))
        summaries.append(
            {
                "deployment_id": deployment.deployment_id,
                "model_id": deployment.model_id,
                "attempts": aggregation.attempt_count,
                "successful_attempts": aggregation.successful_attempts,
                "accuracy": aggregation.success_rate,
                "router_response_cost_usd": deployment_cost,
                "ledger_fingerprint": aggregation.fingerprint,
                "efficiency_record_count": len(aggregation.efficiency_records),
                "economics_record_count": len(aggregation.economics_records),
                "diagnostics": aggregation.diagnostics,
            }
        )
    if not math.isclose(total_cost, summarized_cost, rel_tol=0, abs_tol=1e-12):
        raise RunnerError("deployment cost summaries do not reconcile to run results")
    summary: dict[str, Any] = {
        "run_id": run_id,
        "evaluation_date": evaluation_date.isoformat(),
        "task_pack_fingerprint": pack.fingerprint,
        "run_manifest_fingerprint": manifest.fingerprint,
        "deployment_summaries": summaries,
        "router_response_cost_total_usd": total_cost,
        "account_credit_delta_usd": credit_delta,
        "credit_delta_reconciles": billing_reconciled,
        "billing_reconciliation_abs_tolerance_usd": (
            BILLING_RECONCILIATION_ABS_TOLERANCE_USD
        ),
        "billing_evidence_promoted": billing_reconciled,
        "economics_admission": (
            "provider billing record: response usage and authenticated generation costs "
            "reconcile to the account credit ledger"
            if billing_reconciled
            else "diagnostic only: generation costs do not reconcile to the account credit ledger"
        ),
    }
    summary["fingerprint"] = canonical_fingerprint(summary)
    summary_path = output_dir / "run-summary.json"
    if summary_path.exists():
        if _read_json(summary_path) != summary:
            raise RunnerError(f"run summary drift: {summary_path}")
    else:
        _write_new(summary_path, summary)
    return summary


def _remaining_cost(
    output_dir: Path,
    pack: ControlledTaskPack,
    manifest: OperationalRunManifest,
) -> float:
    costs = []
    for task, deployment in execution_schedule(pack, manifest):
        directory = _attempt_directory(output_dir, task, deployment)
        if (directory / "response.json").exists():
            continue
        costs.append(maximum_request_cost_usd(task, deployment))
    return math.ceil(math.fsum(costs) * 1_000_000) / 1_000_000


def _billing_reconciliation(
    attempt_costs: list[float],
    credits_before: dict[str, Any],
    credits_after: dict[str, Any],
) -> tuple[float, float, bool]:
    total_cost = math.fsum(attempt_costs)
    credit_delta = float(credits_before["remaining_credits"]) - float(
        credits_after["remaining_credits"]
    )
    reconciled = math.isclose(
        total_cost,
        credit_delta,
        rel_tol=0,
        abs_tol=BILLING_RECONCILIATION_ABS_TOLERANCE_USD,
    )
    return total_cost, credit_delta, reconciled


def _execute(args: argparse.Namespace) -> int:
    pack = load_task_pack(args.task_pack)
    manifest = load_run_manifest(args.run_manifest)
    if manifest.harness_version != RUNNER_CONTRACT_VERSION:
        raise RunnerError(
            f"manifest harness {manifest.harness_version} does not match runner "
            f"{RUNNER_CONTRACT_VERSION}"
        )
    api_key = _api_key(manifest)
    report, raw_endpoint_facts = _live_preflight(pack, manifest, api_key)
    if args.preflight:
        print(json.dumps(report, indent=2, sort_keys=True, allow_nan=False))
        return 0 if report["live_endpoint_contracts_valid"] else 1
    if not args.accept_cost:
        raise RunnerError("--accept-cost is required for execution")
    if (
        args.max_cost_usd is None
        or not math.isfinite(args.max_cost_usd)
        or args.max_cost_usd < 0
    ):
        raise RunnerError("--max-cost-usd with a nonnegative value is required")
    try:
        evaluation_date = date.fromisoformat(args.evaluation_date)
    except ValueError as error:
        raise RunnerError("--evaluation-date must be an ISO date") from error
    output_dir = Path(args.output_dir)
    _initialize_run(
        output_dir,
        args.run_id,
        evaluation_date,
        pack,
        manifest,
        resume=args.resume,
    )
    remaining_cost = _remaining_cost(output_dir, pack, manifest)
    if args.max_cost_usd < remaining_cost:
        raise RunnerError(
            f"authorized cost ${args.max_cost_usd:.6f} is below the remaining ceiling "
            f"${remaining_cost:.6f}"
        )
    current_credits = cast(dict[str, Any], report["credits"])
    if float(current_credits["remaining_credits"]) < remaining_cost:
        raise RunnerError(
            f"insufficient credits: ${current_credits['remaining_credits']:.6f} available, "
            f"${remaining_cost:.6f} required by the conservative ceiling"
        )
    endpoint_path = output_dir / "live-endpoint-preflight.json"
    endpoint_artifact = {
        "manifest_fingerprint": manifest.fingerprint,
        "verified_deployments": report["verified_deployments"],
        "raw": raw_endpoint_facts,
    }
    endpoint_artifact["fingerprint"] = canonical_fingerprint(endpoint_artifact)
    if endpoint_path.exists():
        retained_endpoint = _read_json(endpoint_path)
        if (
            retained_endpoint.get("manifest_fingerprint") != manifest.fingerprint
            or canonical_fingerprint(retained_endpoint)
            != retained_endpoint.get("fingerprint")
        ):
            raise RunnerError("retained live endpoint preflight is invalid")
    else:
        _write_new(endpoint_path, endpoint_artifact)
    credits_before_path = output_dir / "credits-before.json"
    if credits_before_path.exists():
        credits_before = _read_fingerprinted(credits_before_path)
    else:
        credits_before = _fingerprinted(current_credits)
        _write_new(credits_before_path, credits_before)
    for index, (task, deployment) in enumerate(execution_schedule(pack, manifest), start=1):
        result = _perform_attempt(
            output_dir,
            str(manifest.api_base_url).rstrip("/"),
            api_key,
            task,
            deployment,
        )
        print(
            json.dumps(
                {
                    "completed": index,
                    "total": len(pack.tasks) * len(manifest.deployments),
                    "task_id": task.task_id,
                    "deployment_id": deployment.deployment_id,
                    "success": result["success"],
                },
                sort_keys=True,
            ),
            flush=True,
        )
    credits_after_path = output_dir / "credits-after.json"
    if credits_after_path.exists():
        credits_after = _read_fingerprinted(credits_after_path)
    else:
        credits_after = _fingerprinted(
            _credits(str(manifest.api_base_url).rstrip("/"), api_key)
        )
        _write_new(credits_after_path, credits_after)
    summary = _finalize(
        output_dir,
        args.run_id,
        evaluation_date,
        pack,
        manifest,
        credits_before,
        credits_after,
    )
    print(json.dumps(summary, indent=2, sort_keys=True, allow_nan=False))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Preflight or execute the exact, cost-gated OpenRouter five-model pilot"
    )
    parser.add_argument("--task-pack", required=True)
    parser.add_argument("--run-manifest", required=True)
    parser.add_argument(
        "--accept-network",
        action="store_true",
        help="Required acknowledgement for live OpenRouter metadata/account access",
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--preflight", action="store_true")
    mode.add_argument("--execute", action="store_true")
    parser.add_argument("--accept-cost", action="store_true")
    parser.add_argument("--max-cost-usd", type=float)
    parser.add_argument("--run-id")
    parser.add_argument("--evaluation-date")
    parser.add_argument("--output-dir")
    parser.add_argument("--resume", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    if not args.accept_network:
        raise RunnerError("--accept-network is required")
    if args.execute and not all((args.run_id, args.evaluation_date, args.output_dir)):
        raise RunnerError("execution requires --run-id, --evaluation-date, and --output-dir")
    return _execute(args)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RunnerError, urllib.error.HTTPError, urllib.error.URLError) as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(2) from error
