from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable

from umi.config import ProjectConfig
from umi.schemas import EvidenceBenchmarkSeries, EvidenceProfile, Provenance


def _digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), default=str).encode()
    ).hexdigest()


def capability_profile(
    series: Iterable[EvidenceBenchmarkSeries],
    records: Iterable[Provenance],
    config: ProjectConfig,
) -> EvidenceProfile:
    ordered_series = tuple(
        sorted(series, key=lambda item: (item.benchmark_id, item.cohort_key))
    )
    ordered_records = tuple(sorted(records, key=lambda item: item.record_id))
    methodology = {
        "estimate_scope": "capability",
        "benchmark_series": [item.model_dump(mode="json") for item in ordered_series],
        "config_fingerprint": config.fingerprint,
    }
    methodology_fingerprint = _digest(methodology)
    evidence_record_fingerprint = _digest(
        [item.model_dump(mode="json") for item in ordered_records]
    )
    return EvidenceProfile(
        id=methodology_fingerprint,
        estimate_scope="capability",
        benchmark_series=ordered_series,
        domain_ids=tuple(
            sorted({item.domain for item in ordered_series}, key=lambda item: item.value)
        ),
        family_ids=tuple(sorted({item.family for item in ordered_series})),
        source_organizations=tuple(sorted({item.source.organization for item in ordered_records})),
        contributing_record_ids=tuple(item.record_id for item in ordered_records),
        methodology_fingerprint=methodology_fingerprint,
        evidence_record_fingerprint=evidence_record_fingerprint,
    )


def workload_profile(
    estimate_scope: str,
    workload_series: Iterable[str],
    records: Iterable[Provenance],
    config: ProjectConfig,
) -> EvidenceProfile:
    ordered_series = tuple(sorted(set(workload_series)))
    ordered_records = tuple(sorted(records, key=lambda item: item.record_id))
    methodology = {
        "estimate_scope": estimate_scope,
        "workload_series": ordered_series,
        "config_fingerprint": config.fingerprint,
    }
    methodology_fingerprint = _digest(methodology)
    evidence_record_fingerprint = _digest(
        [item.model_dump(mode="json") for item in ordered_records]
    )
    return EvidenceProfile(
        id=methodology_fingerprint,
        estimate_scope=estimate_scope,
        workload_series=ordered_series,
        source_organizations=tuple(sorted({item.source.organization for item in ordered_records})),
        contributing_record_ids=tuple(item.record_id for item in ordered_records),
        methodology_fingerprint=methodology_fingerprint,
        evidence_record_fingerprint=evidence_record_fingerprint,
    )
