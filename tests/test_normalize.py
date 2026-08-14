import pytest

from umi.normalize import normalize_cohort
from umi.schemas import Direction


def test_robust_z_is_deterministic_and_directional() -> None:
    values = {f"m{index}": float(index) for index in range(1, 9)}
    first = normalize_cohort(values, direction=Direction.HIGHER)
    second = normalize_cohort(dict(reversed(list(values.items()))), direction=Direction.HIGHER)
    assert first.method == "robust_z"
    assert first.scores == second.scores
    assert first.scores["m8"] > first.scores["m1"]  # type: ignore[operator]


def test_small_cohort_uses_average_rank_percentiles_and_marks_provisional() -> None:
    result = normalize_cohort({"a": 10, "b": 10, "c": 20}, direction=Direction.HIGHER)
    assert result.method == "percentile"
    assert result.provisional
    assert result.scores == {"a": 25.0, "b": 25.0, "c": 100.0}


def test_singleton_is_unscored() -> None:
    result = normalize_cohort({"only": 1}, direction=Direction.HIGHER)
    assert result.scores == {"only": None}
    assert result.method == "singleton"


def test_zero_mad_falls_back_to_percentiles() -> None:
    result = normalize_cohort(
        {"a": 1, "b": 1, "c": 1, "d": 1, "e": 1, "f": 1, "g": 1, "h": 2},
        direction=Direction.HIGHER,
    )
    assert result.method == "percentile_zero_mad"
    assert result.scores["h"] == 100.0


def test_positive_infinity_is_worst_for_lower_is_better() -> None:
    result = normalize_cohort(
        {"failed": float("inf"), "a": 1, "b": 2, "c": 3, "d": 4, "e": 5},
        direction=Direction.LOWER,
        log_transform=True,
    )
    assert result.scores["failed"] == 0.0


def test_log_transform_rejects_negative_values() -> None:
    with pytest.raises(ValueError, match="nonnegative"):
        normalize_cohort({"a": -1, "b": 1}, direction=Direction.LOWER, log_transform=True)
