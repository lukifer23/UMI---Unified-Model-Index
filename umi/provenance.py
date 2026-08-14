from __future__ import annotations

from collections.abc import Iterable
from typing import TypeVar

from umi.schemas import Provenance, ResultType

QUALITY_TYPES = {ResultType.INDEPENDENT, ResultType.COMMUNITY}
P = TypeVar("P", bound=Provenance)
TIER_ORDER = (
    ResultType.INDEPENDENT,
    ResultType.COMMUNITY,
    ResultType.VENDOR,
    ResultType.DERIVED,
)


def evidence_quality_share(records: Iterable[Provenance]) -> float:
    items = list(records)
    if not items:
        return 0.0
    return sum(item.result_type in QUALITY_TYPES for item in items) / len(items)


def select_best_tier(records: Iterable[P]) -> list[P]:
    items = list(records)
    for tier in TIER_ORDER:
        selected = [item for item in items if item.result_type == tier]
        if selected:
            return selected
    return []
