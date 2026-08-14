from __future__ import annotations

from dataclasses import dataclass
from statistics import median
from typing import TypeVar

from umi.provenance import select_best_tier
from umi.schemas import ComponentScore, Domain, Provenance

P = TypeVar("P", bound=Provenance)


@dataclass(frozen=True)
class ComponentComputation:
    components: dict[str, ComponentScore]
    evidence: dict[str, tuple[Provenance, ...]]
    domains: dict[str, tuple[Domain, ...]]


def weighted_available(
    values: dict[str, float | None], weights: dict[str, float]
) -> tuple[float | None, float]:
    present = {key: value for key, value in values.items() if value is not None and key in weights}
    available_weight = sum(weights[key] for key in present)
    total_weight = sum(weights.values())
    if not present or available_weight == 0 or total_weight == 0:
        return None, 0.0
    score = sum(float(value) * weights[key] for key, value in present.items()) / available_weight
    return score, available_weight / total_weight


def consolidate_numeric(records: list[P], attribute: str) -> tuple[float | None, list[P], bool]:
    selected = [
        record for record in select_best_tier(records) if isinstance(record, type(records[0]))
    ]
    values = [getattr(record, attribute) for record in selected]
    finite_values = [float(value) for value in values if value is not None]
    return (median(finite_values) if finite_values else None, selected, len(records) > 1)
