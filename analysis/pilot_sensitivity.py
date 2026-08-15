from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass

from umi.config import ProjectConfig
from umi.loading import Dataset
from umi.schemas import Domain
from umi.scoring import score_dataset


@dataclass(frozen=True)
class PilotSensitivityResult:
    scenario: str
    model_id: str
    baseline_evidence_profile_id: str | None
    scenario_evidence_profile_id: str | None
    baseline_score_scale_id: str | None
    scenario_score_scale_id: str | None
    support_changed: bool
    scale_changed: bool
    baseline_coverage: float
    scenario_coverage: float
    coverage_change: float
    baseline_score: float | None
    scenario_score: float | None
    raw_score_change: float | None
    score_change_comparable: bool
    scenario_informative: bool
    reason: str
    capability_score: float | None
    baseline_change: float | None
    headline_overall: float | None


def _equal_family_config(config: ProjectConfig) -> ProjectConfig:
    families = []
    for family in config.families:
        positive = [
            item for item in config.families if item.domain == family.domain and item.weight > 0
        ]
        weight = (1.0 / len(positive)) if family.weight > 0 else 0.0
        families.append(family.model_copy(update={"weight": weight, "cap": max(1.0, weight)}))
    fingerprint = hashlib.sha256(
        json.dumps(
            {
                "base_config_fingerprint": config.fingerprint,
                "scenario": "equal_family",
                "families": [item.model_dump(mode="json") for item in families],
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
    ).hexdigest()
    return config.model_copy(
        update={"families": tuple(families), "fingerprint": fingerprint}
    )


def analyze_pilot_sensitivity(
    dataset: Dataset, config: ProjectConfig
) -> list[PilotSensitivityResult]:
    baseline = {item.model_id: item for item in score_dataset(dataset, config)}
    scenarios: list[tuple[str, Dataset, ProjectConfig]] = [
        ("equal_family", dataset, _equal_family_config(config))
    ]
    source_ids = sorted(
        {
            item.source_artifact_id
            for item in (*dataset.benchmarks, *dataset.efficiency, *dataset.task_economics)
            if item.source_artifact_id is not None
        }
    )
    for source_id in source_ids:
        scenarios.append(
            (
                f"ablate_{source_id}",
                dataset.model_copy(
                    update={
                        "benchmarks": tuple(
                            item
                            for item in dataset.benchmarks
                            if item.source_artifact_id != source_id
                        ),
                        "efficiency": tuple(
                            item
                            for item in dataset.efficiency
                            if item.source_artifact_id != source_id
                        ),
                        "task_economics": tuple(
                            item
                            for item in dataset.task_economics
                            if item.source_artifact_id != source_id
                        ),
                    }
                ),
                config,
            )
        )
    output: list[PilotSensitivityResult] = []
    for scenario, scenario_dataset, scenario_config in scenarios:
        scenario_results = score_dataset(scenario_dataset, scenario_config)
        for item in scenario_results:
            baseline_score = baseline[item.model_id].capability.score
            score = item.capability.score
            baseline_component = baseline[item.model_id].capability
            scenario_component = item.capability
            baseline_series = (
                baseline_component.evidence_profile.benchmark_series
                if baseline_component.evidence_profile is not None
                else ()
            )
            scenario_series = (
                scenario_component.evidence_profile.benchmark_series
                if scenario_component.evidence_profile is not None
                else ()
            )
            support_changed = baseline_series != scenario_series
            scale_changed = baseline_component.score_scale_id != scenario_component.score_scale_id
            raw_change = (
                score - baseline_score
                if score is not None and baseline_score is not None
                else None
            )
            comparable = (
                raw_change is not None and not support_changed and not scale_changed
            )
            informative = (
                bool(raw_change is not None and abs(raw_change) > 1e-12)
                if scenario == "equal_family"
                else bool(
                    support_changed
                    or (raw_change is not None and abs(raw_change) > 1e-12)
                    or abs(scenario_component.coverage - baseline_component.coverage) > 1e-12
                )
            )
            reason = (
                "support changed; raw score change is diagnostic only"
                if support_changed
                else "score scale changed; raw score change is diagnostic only"
                if scale_changed
                else "comparable score change"
                if raw_change is not None and abs(raw_change) > 1e-12
                else "score scale changed but active support and score did not"
                if scale_changed
                else "no effect on this model's active evidence"
            )
            output.append(
                PilotSensitivityResult(
                    scenario=scenario,
                    model_id=item.model_id,
                    baseline_evidence_profile_id=baseline_component.evidence_profile_id,
                    scenario_evidence_profile_id=scenario_component.evidence_profile_id,
                    baseline_score_scale_id=baseline_component.score_scale_id,
                    scenario_score_scale_id=scenario_component.score_scale_id,
                    support_changed=support_changed,
                    scale_changed=scale_changed,
                    baseline_coverage=baseline_component.coverage,
                    scenario_coverage=scenario_component.coverage,
                    coverage_change=scenario_component.coverage - baseline_component.coverage,
                    baseline_score=baseline_score,
                    scenario_score=score,
                    raw_score_change=raw_change,
                    score_change_comparable=comparable,
                    scenario_informative=informative,
                    reason=reason,
                    capability_score=score,
                    baseline_change=raw_change,
                    headline_overall=item.headline_overall,
                )
            )
    return sorted(output, key=lambda item: (item.scenario, item.model_id))


def family_budget_snapshot(config: ProjectConfig) -> dict[Domain, dict[str, float]]:
    return {
        domain: {
            item.id: item.weight for item in config.families if item.domain == domain
        }
        for domain in Domain
    }
