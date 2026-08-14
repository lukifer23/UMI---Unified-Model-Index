from __future__ import annotations

from dataclasses import dataclass

from umi.config import ProjectConfig
from umi.loading import Dataset
from umi.schemas import Domain
from umi.scoring import score_dataset


@dataclass(frozen=True)
class PilotSensitivityResult:
    scenario: str
    model_id: str
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
    return config.model_copy(update={"families": tuple(families)})


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
            output.append(
                PilotSensitivityResult(
                    scenario=scenario,
                    model_id=item.model_id,
                    capability_score=score,
                    baseline_change=(
                        score - baseline_score
                        if score is not None and baseline_score is not None
                        else None
                    ),
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
