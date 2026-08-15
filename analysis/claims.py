from __future__ import annotations

from umi.loading import Dataset
from umi.readiness import is_scoring_ready
from umi.schemas import ResultType


def calibrate_release_claims(dataset: Dataset) -> list[dict[str, object]]:
    """Compare claims only with exact ready independent/community measurements."""
    models = {model.id: model for model in dataset.models}
    output: list[dict[str, object]] = []
    for claim in sorted(dataset.release_claims, key=lambda item: item.record_id):
        external = [
            record
            for record in dataset.benchmarks
            if record.model_id == claim.model_id
            and record.result_type in {ResultType.INDEPENDENT, ResultType.COMMUNITY}
        ]
        filters = (
            ("no_external_measurement", external),
            (
                "benchmark_mismatch",
                [item for item in external if item.benchmark_id == claim.benchmark_id],
            ),
        )
        reason = "no_external_measurement"
        candidates = external
        for failure_reason, filtered in filters:
            if not filtered:
                reason = failure_reason
                break
            candidates = filtered
        else:
            checks = (
                ("cohort_mismatch", "cohort_key", claim.cohort_key),
                ("unit_mismatch", "unit", claim.unit),
                ("direction_mismatch", "direction", claim.direction),
                ("date_incompatible", "evaluation_date", claim.evaluation_date),
            )
            for failure_reason, attribute, expected in checks:
                filtered = [
                    item for item in candidates if getattr(item, attribute) == expected
                ]
                if not filtered:
                    reason = failure_reason
                    break
                candidates = filtered
            else:
                matches = [
                    item
                    for item in candidates
                    if is_scoring_ready(item, models[item.model_id])
                ]
                reason = "external_record_unready"
                if matches:
                    record = min(matches, key=lambda item: item.record_id)
                    output.append(
                        {
                            "claim_record_id": claim.record_id,
                            "measurement_record_id": record.record_id,
                            "status": "compared",
                            "signed_difference": record.value - claim.value,
                            "absolute_difference": abs(record.value - claim.value),
                        }
                    )
                    continue
        output.append(
            {
                "claim_record_id": claim.record_id,
                "status": "not_comparable",
                "reason": reason,
            }
        )
    return output
