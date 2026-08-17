"""Typed Public evidence contracts bound to the frozen Epoch zip."""

from __future__ import annotations

import math

from pydantic import Field, model_validator

from umi.edition import ConfigModel


class PublicEvidenceRecord(ConfigModel):
    series_id: str
    config_id: str
    entity_id: str | None = None
    raw: float
    complete: bool
    source_name: str
    member: str
    field: str
    source_artifact_id: str
    source_artifact_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def reject_nonfinite_or_invented_rows(self) -> PublicEvidenceRecord:
        if not math.isfinite(self.raw):
            raise ValueError(f"{self.series_id}/{self.config_id} raw is not finite")
        return self


class PublicSeriesContract(ConfigModel):
    series_id: str
    member: str
    field: str
    kind: str
    component: str
    harness: str | None = None
    panel_filter: str | None = None
    anchor_n: int = Field(ge=0)
    accepted_entity_ids: tuple[str, ...]
    records: tuple[PublicEvidenceRecord, ...]

    @model_validator(mode="after")
    def bind_records_to_the_series(self) -> PublicSeriesContract:
        if self.anchor_n != len(self.records):
            raise ValueError(f"{self.series_id} anchor_n does not match records")
        accepted = tuple(
            item.entity_id for item in self.records if item.entity_id is not None
        )
        if accepted != self.accepted_entity_ids:
            raise ValueError(f"{self.series_id} accepted_entity_ids drifted from records")
        for item in self.records:
            if item.series_id != self.series_id or item.member != self.member:
                raise ValueError(f"{self.series_id} record is bound to the wrong extract")
            if item.field != self.field:
                raise ValueError(f"{self.series_id} record field does not match the contract")
        return self
