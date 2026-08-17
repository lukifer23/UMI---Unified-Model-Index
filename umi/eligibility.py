"""Single eligibility decision object for v0.3 and v0.4."""

from __future__ import annotations

from umi.config import OverallWeights, ProjectConfig
from umi.edition import ConfigModel
from umi.schemas import ScoringResult
from umi.scoring import eligible_for_weights


class EligibilityDecision(ConfigModel):
    eligible: bool
    reason_codes: tuple[str, ...]
    details: dict[str, str]


def decide_legacy_eligibility(
    result: ScoringResult, config: ProjectConfig, weights: OverallWeights
) -> EligibilityDecision:
    reasons: list[str] = []
    if not result.scoring_ready:
        reasons.append("not_scoring_ready")
    if result.capability.score is None:
        reasons.append("capability_missing")
    if result.efficiency.score is None:
        reasons.append("efficiency_missing")
    if result.economics.score is None:
        reasons.append("economics_missing")
    if not eligible_for_weights(result, config, weights) and not reasons:
        reasons.append("legacy_publication_gates")
    eligible = eligible_for_weights(result, config, weights)
    return EligibilityDecision(
        eligible=eligible,
        reason_codes=tuple(reasons) if not eligible else (),
        details={"edition": "v0.3"},
    )
