"""Offline diagnostic review for the licensed RootCauseBench v3 final-trial ledger.

The review purposefully does not create scored UMI records. The source omits the
explicit inference effort, deployment/billing reconciliation, and request/retry
history required by the canonical five-Max-pilot scoring contract.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
from typing import Any, cast

import yaml
from pydantic import Field, model_validator

from umi.schemas import StrictModel

ROOT = Path(__file__).resolve().parents[1]
SOURCE_URL = "https://github.com/edgedelta/root-cause-bench"
SOURCE_COMMIT = "0c3c476e4627978dc54b5c047fd488d40561b4e5"
REVIEW_VERSION = "rootcausebench-v3-diagnostic-review-v1"
FILES = {
    "rootcausebench-v3-results-2026-08-16": "rootcausebench-v3-results.json",
    "rootcausebench-v3-config-2026-08-16": "rootcausebench-v3-leaderboard-v2-docker.yaml",
    "rootcausebench-v3-readme-2026-08-16": "rootcausebench-v3-README.md",
    "rootcausebench-v3-license-2026-08-16": "rootcausebench-v3-LICENSE",
}
TARGET_ROUTES = {
    "claude-fable-5-max": "openrouter/anthropic/claude-fable-5",
    "claude-opus-5-max": "openrouter/anthropic/claude-opus-5",
    "gpt-5.6-sol-max": "openrouter/openai/gpt-5.6-sol",
    "kimi-k3-max": "openrouter/moonshotai/kimi-k3",
    "glm-5.2-max": "openrouter/z-ai/glm-5.2",
}
RESOURCE_FIELDS = (
    ("InputTokens", "input_tokens", "tokens"),
    ("OutputTokens", "output_tokens", "tokens"),
    ("CacheTokens", "cache_tokens", "tokens"),
    ("DurationSec", "duration_seconds", "seconds"),
    ("CostUSD", "router_reported_cost_usd", "usd"),
)


class ResourceObservationSummary(StrictModel):
    field_id: str
    source_column: str
    unit: str
    observation_count: int = Field(ge=1)
    total: float = Field(ge=0)
    attempted_mean: float = Field(ge=0)
    success_adjusted_mean: float = Field(ge=0)
    minimum: float = Field(ge=0)
    maximum: float = Field(ge=0)

    @model_validator(mode="after")
    def validate_summary(self) -> ResourceObservationSummary:
        if self.minimum > self.maximum:
            raise ValueError("resource minimum cannot exceed maximum")
        if self.success_adjusted_mean < self.attempted_mean:
            raise ValueError("success-adjusted resource mean cannot be below attempted mean")
        return self


class RootCauseBenchModelReview(StrictModel):
    candidate_pilot_id: str
    source_model_id: str
    configured_agent: str
    attempts: int = Field(ge=1)
    successful_final_trials: int = Field(ge=1)
    pass_rate: float = Field(ge=0, le=1)
    mean_graded_reward: float = Field(ge=0, le=1)
    task_count: int = Field(ge=1)
    attempts_per_task: int = Field(ge=1)
    unique_trial_directories: int = Field(ge=1)
    final_trial_errors: int = Field(ge=0)
    resource_observations: tuple[ResourceObservationSummary, ...]
    explicit_inference_effort: str | None = None
    exact_pilot_configuration_match: bool
    efficiency_admitted: bool
    economics_admitted: bool
    scoring_disposition: str
    diagnostics: tuple[str, ...]

    @model_validator(mode="after")
    def preserve_abstention(self) -> RootCauseBenchModelReview:
        if self.successful_final_trials > self.attempts:
            raise ValueError("successful final trials cannot exceed attempts")
        if any(item.observation_count != self.attempts for item in self.resource_observations):
            raise ValueError("each resource field must observe every final trial")
        expected_resources = tuple(item[1] for item in RESOURCE_FIELDS)
        if tuple(item.field_id for item in self.resource_observations) != expected_resources:
            raise ValueError("every required resource field must be retained in source order")
        if self.explicit_inference_effort is not None:
            raise ValueError("the frozen config must not infer an effort setting")
        if (
            self.exact_pilot_configuration_match
            or self.efficiency_admitted
            or self.economics_admitted
        ):
            raise ValueError("RootCauseBench v3 is diagnostic-only for exact Max pilots")
        if self.scoring_disposition != "diagnostic_only":
            raise ValueError("RootCauseBench v3 must remain diagnostic_only")
        return self


class RootCauseBenchReview(StrictModel):
    report_version: str
    source_url: str
    source_commit: str = Field(pattern=r"^[0-9a-f]{40}$")
    source_artifact_ids: tuple[str, ...]
    source_artifact_sha256: dict[str, str]
    license_id: str
    redistribution_scope: str
    final_trial_row_count: int = Field(ge=1)
    full_cohort_model_count: int = Field(ge=8)
    anchor_cohort_sufficient: bool
    configured_attempts_per_task: int = Field(ge=1)
    configured_timeout_seconds: int = Field(ge=1)
    models: tuple[RootCauseBenchModelReview, ...]
    scoring_disposition: str
    headline_eligible: bool
    headline_overall: float | None = None
    blockers: tuple[str, ...]
    review_fingerprint: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def validate_review(self) -> RootCauseBenchReview:
        if self.source_url != SOURCE_URL or self.source_commit != SOURCE_COMMIT:
            raise ValueError("review must bind the pinned RootCauseBench source")
        if self.license_id != "Apache-2.0" or self.redistribution_scope != "full_artifact":
            raise ValueError("review requires the verified Apache-2.0 full artifact")
        if not self.anchor_cohort_sufficient:
            raise ValueError("review requires an 8-plus anchor cohort")
        if tuple(item.candidate_pilot_id for item in self.models) != tuple(TARGET_ROUTES):
            raise ValueError("review must retain all five target routes")
        if self.scoring_disposition != "diagnostic_only":
            raise ValueError("review must remain diagnostic_only")
        if self.headline_eligible or self.headline_overall is not None:
            raise ValueError("review must not emit a UMI headline")
        return self


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _fingerprint(payload: dict[str, Any]) -> str:
    rendered = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def _nonnegative(row: dict[str, Any], field: str) -> float:
    value = row[field]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"RootCauseBench {field} must be numeric")
    number = float(value)
    if not math.isfinite(number) or number < 0:
        raise ValueError(f"RootCauseBench {field} must be finite and non-negative")
    return number


def _load_rows(path: Path) -> tuple[dict[str, Any], ...]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    required = {
        "Attempt",
        "CacheTokens",
        "CostUSD",
        "DurationSec",
        "Error",
        "GradedReward",
        "InputTokens",
        "ModelName",
        "OutputTokens",
        "Passed",
        "TaskName",
        "TrialDir",
    }
    if not isinstance(payload, list) or not payload:
        raise ValueError("RootCauseBench results must be a non-empty JSON list")
    rows: list[dict[str, Any]] = []
    for index, item in enumerate(payload):
        if not isinstance(item, dict):
            raise ValueError(f"RootCauseBench row {index} must be an object")
        missing = sorted(required - set(item))
        if missing:
            raise ValueError(f"RootCauseBench row {index} misses: {', '.join(missing)}")
        rows.append(cast(dict[str, Any], item))
    return tuple(rows)


def _load_config(path: Path) -> tuple[int, int, dict[str, dict[str, Any]]]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("RootCauseBench config must be a mapping")
    attempts = payload.get("n_attempts")
    agents = payload.get("agents")
    if isinstance(attempts, bool) or not isinstance(attempts, int) or attempts < 1:
        raise ValueError("RootCauseBench n_attempts must be positive")
    if not isinstance(agents, list):
        raise ValueError("RootCauseBench agents must be a list")
    mapped: dict[str, dict[str, Any]] = {}
    for item in agents:
        if not isinstance(item, dict):
            raise ValueError("RootCauseBench agent must be an object")
        model_name, timeout = item.get("model_name"), item.get("override_timeout_sec")
        if not isinstance(model_name, str) or not model_name:
            raise ValueError("RootCauseBench agent needs model_name")
        if isinstance(timeout, bool) or not isinstance(timeout, int) or timeout < 1:
            raise ValueError("RootCauseBench agent needs a positive timeout")
        if model_name in mapped:
            raise ValueError(f"RootCauseBench duplicates {model_name}")
        mapped[model_name] = cast(dict[str, Any], item)
    timeouts = {int(item["override_timeout_sec"]) for item in mapped.values()}
    if len(timeouts) != 1:
        raise ValueError("RootCauseBench requires one frozen timeout")
    return attempts, timeouts.pop(), mapped


def _resource(
    rows: tuple[dict[str, Any], ...], column: str, field: str, unit: str, successes: int
) -> ResourceObservationSummary:
    values = tuple(_nonnegative(row, column) for row in rows)
    total = sum(values)
    return ResourceObservationSummary(
        field_id=field,
        source_column=column,
        unit=unit,
        observation_count=len(values),
        total=total,
        attempted_mean=total / len(values),
        success_adjusted_mean=total / successes,
        minimum=min(values),
        maximum=max(values),
    )


def build_rootcausebench_review(root: Path = ROOT) -> dict[str, Any]:
    source_dir = root / "data" / "sources" / "v0.6"
    paths = {artifact_id: source_dir / filename for artifact_id, filename in FILES.items()}
    rows = _load_rows(paths["rootcausebench-v3-results-2026-08-16"])
    attempts_per_task, timeout_seconds, agents = _load_config(
        paths["rootcausebench-v3-config-2026-08-16"]
    )
    if "Apache License" not in paths["rootcausebench-v3-license-2026-08-16"].read_text(
        encoding="utf-8"
    ):
        raise ValueError("RootCauseBench frozen license text is not Apache")
    if "Frozen run (v3)" not in paths["rootcausebench-v3-readme-2026-08-16"].read_text(
        encoding="utf-8"
    ):
        raise ValueError("RootCauseBench README lacks its frozen v3 declaration")
    source_models = {str(row["ModelName"]) for row in rows}
    if source_models != set(agents):
        raise ValueError("RootCauseBench results do not reconcile to its frozen agent config")

    models: list[RootCauseBenchModelReview] = []
    for pilot_id, source_model_id in TARGET_ROUTES.items():
        agent = agents.get(source_model_id)
        if agent is None or agent.get("name") != "terminus-2":
            raise ValueError(f"RootCauseBench target {source_model_id} lacks terminus-2 config")
        if any(
            key in agent for key in ("reasoning_effort", "kwargs", "agent_kwargs", "model_kwargs")
        ):
            raise ValueError("frozen RootCauseBench config changed; review effort binding")
        model_rows = tuple(row for row in rows if row["ModelName"] == source_model_id)
        task_count = len({str(row["TaskName"]) for row in model_rows})
        if {row["Attempt"] for row in model_rows} != set(range(1, attempts_per_task + 1)):
            raise ValueError(f"RootCauseBench {source_model_id} misses a configured attempt")
        if len(model_rows) != task_count * attempts_per_task:
            raise ValueError(f"RootCauseBench {source_model_id} has an incomplete final-trial grid")
        if any(not isinstance(row["Passed"], bool) for row in model_rows):
            raise ValueError(f"RootCauseBench {source_model_id} has non-boolean Passed")
        successes = sum(bool(row["Passed"]) for row in model_rows)
        if successes == 0:
            raise ValueError(f"RootCauseBench {source_model_id} has no successful final trial")
        rewards = tuple(_nonnegative(row, "GradedReward") for row in model_rows)
        if any(value > 1 for value in rewards):
            raise ValueError(f"RootCauseBench {source_model_id} reward exceeds one")
        resources = tuple(_resource(model_rows, *item, successes) for item in RESOURCE_FIELDS)
        models.append(
            RootCauseBenchModelReview(
                candidate_pilot_id=pilot_id,
                source_model_id=source_model_id,
                configured_agent="terminus-2",
                attempts=len(model_rows),
                successful_final_trials=successes,
                pass_rate=successes / len(model_rows),
                mean_graded_reward=sum(rewards) / len(rewards),
                task_count=task_count,
                attempts_per_task=attempts_per_task,
                unique_trial_directories=len({str(row["TrialDir"]) for row in model_rows}),
                final_trial_errors=sum(bool(str(row["Error"]).strip()) for row in model_rows),
                resource_observations=resources,
                explicit_inference_effort=None,
                exact_pilot_configuration_match=False,
                efficiency_admitted=False,
                economics_admitted=False,
                scoring_disposition="diagnostic_only",
                diagnostics=(
                    "OpenRouter route is frozen, but no explicit inference effort crosswalks it "
                    "to the canonical Max pilot.",
                    "No immutable provider snapshot, endpoint, service tier, or run-level "
                    "fallback record is retained.",
                    "CostUSD is source-reported router cost, not reconciled provider billing "
                    "evidence.",
                    "Final trials omit immutable request/response and retry-history residuals, "
                    "so complete request-level resources cannot be certified.",
                    "Resource values divide all final-trial resources by successful final trials "
                    "and remain diagnostic only.",
                ),
            )
        )
    artifact_sha256 = {artifact_id: _sha256(path) for artifact_id, path in paths.items()}
    payload: dict[str, Any] = {
        "report_version": REVIEW_VERSION,
        "source_url": SOURCE_URL,
        "source_commit": SOURCE_COMMIT,
        "source_artifact_ids": tuple(artifact_sha256),
        "source_artifact_sha256": artifact_sha256,
        "license_id": "Apache-2.0",
        "redistribution_scope": "full_artifact",
        "final_trial_row_count": len(rows),
        "full_cohort_model_count": len(source_models),
        "anchor_cohort_sufficient": len(source_models) >= 8,
        "configured_attempts_per_task": attempts_per_task,
        "configured_timeout_seconds": timeout_seconds,
        "models": [model.model_dump(mode="json") for model in models],
        "scoring_disposition": "diagnostic_only",
        "headline_eligible": False,
        "headline_overall": None,
        "blockers": (
            "missing-explicit-inference-effort",
            "missing-verified-exact-deployment",
            "missing-provider-billing-reconciliation",
            "missing-request-and-retry-history-residuals",
        ),
    }
    payload["review_fingerprint"] = _fingerprint(payload)
    return RootCauseBenchReview.model_validate(payload).model_dump(mode="json")


def render_rootcausebench_review_markdown(review: dict[str, Any]) -> str:
    lines = [
        "# RootCauseBench v3 diagnostic evidence review",
        "",
        "This deterministic offline review validates a licensed, frozen final-trial ledger. "
        "It is not a UMI score and does not change UMI coverage.",
        "",
        f"- source: [{review['source_url']}]({review['source_url']})",
        f"- pinned commit: `{review['source_commit']}`",
        f"- license / retained scope: `{review['license_id']}` / "
        f"`{review['redistribution_scope']}`",
        f"- final trials: `{review['final_trial_row_count']}` across "
        f"`{review['full_cohort_model_count']}` routes",
        f"- profile: `terminus-2`, `{review['configured_attempts_per_task']}` "
        f"attempts/scenario, `{review['configured_timeout_seconds']}s` timeout",
        "",
        "## Observed final-trial diagnostics",
        "",
        "Each resource value is the total across final trials divided by successful final "
        "trials. `CostUSD` is source-reported router cost, never provider billing.",
        "",
        "| Candidate pilot | Source route | Trials | Passed | Pass rate | Reward | "
        "Duration/success (s) | Router cost/success ($) |",
        "|---|---|---:|---:|---:|---:|---:|---:|",
    ]
    for model in review["models"]:
        resources = {item["field_id"]: item for item in model["resource_observations"]}
        lines.append(
            "| `{}` | `{}` | {} | {} | {:.1%} | {:.3f} | {:.1f} | {:.4f} |".format(
                model["candidate_pilot_id"],
                model["source_model_id"],
                model["attempts"],
                model["successful_final_trials"],
                model["pass_rate"],
                model["mean_graded_reward"],
                resources["duration_seconds"]["success_adjusted_mean"],
                resources["router_reported_cost_usd"]["success_adjusted_mean"],
            )
        )
    lines.extend(["", "## Why no UMI score is emitted", ""])
    lines.extend(f"- `{blocker}`" for blocker in review["blockers"])
    lines.extend(
        [
            "",
            "The source records a route and agent, not an effective Max effort or verified "
            "deployment. Its final-trial router costs are diagnostic, and it does not retain "
            "request/retry history sufficient to prove an all-attempt resource or billing ledger.",
        ]
    )
    return "\n".join(lines) + "\n"


def write_rootcausebench_review(
    output_dir: Path | None = None, *, root: Path = ROOT
) -> dict[str, Any]:
    review = build_rootcausebench_review(root)
    destination = output_dir or root / "data" / "editions" / "v0.6" / "processed"
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "rootcausebench-v3-review.json").write_text(
        json.dumps(review, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    if output_dir is None:
        docs_path = root / "docs" / "sources" / "ROOTCAUSEBENCH_V3.md"
        docs_path.parent.mkdir(parents=True, exist_ok=True)
        docs_path.write_text(render_rootcausebench_review_markdown(review), encoding="utf-8")
    return review


def validate_rootcausebench_review(root: Path = ROOT) -> dict[str, Any]:
    review = build_rootcausebench_review(root)
    stored = root / "data" / "editions" / "v0.6" / "processed" / "rootcausebench-v3-review.json"
    valid = stored.is_file() and json.loads(stored.read_text(encoding="utf-8")) == review
    return {
        "valid": valid,
        "scoring_disposition": "diagnostic_only",
        "headline_eligible": False,
        "headline_overall": None,
        "review_fingerprint": review["review_fingerprint"],
    }
