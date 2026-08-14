from __future__ import annotations

from umi.loading import Dataset
from umi.readiness import is_scoring_ready
from umi.schemas import ResultType


def calibrate_release_claims(dataset: Dataset) -> list[dict[str, object]]:
    """Compare claims only with exact ready independent/community measurements."""
    models = {model.id: model for model in dataset.models}
    output: list[dict[str, object]] = []
    for claim in sorted(dataset.release_claims, key=lambda item: item.record_id):
        matches = [
            record
            for record in dataset.benchmarks
            if record.model_id == claim.model_id
            and record.model_snapshot_id == claim.model_snapshot_id
            and record.benchmark_id == claim.benchmark_id
            and record.cohort_key == claim.cohort_key
            and record.evaluation_date == claim.evaluation_date
            and record.result_type in {ResultType.INDEPENDENT, ResultType.COMMUNITY}
            and is_scoring_ready(record, models[record.model_id])
        ]
        if not matches:
            output.append({"claim_record_id": claim.record_id, "status": "not_comparable"})
            continue
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
    return output
