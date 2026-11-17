"""Leakage-safe historical features for a single learner and target concept."""
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from numbers import Real
from math import floor, isfinite, log
from .schemas import Interaction, validate_identifier, validate_milliseconds

FEATURE_NAMES: list[str] = [
    "previous_response_time", "previous_correct",
    "time_since_previous_interaction", "time_since_last_skill_attempt",
    "skill_attempt_count", "skill_avg_response_time", "skill_accuracy",
    "recent_skill_avg_response_time", "recent_skill_accuracy",
    "skill_correct_streak", "overall_accuracy", "overall_attempt_count",
]


def _accuracy(rows: Sequence[Interaction]) -> float | None:
    return sum(row.correct for row in rows) / len(rows) if rows else None


def _mean_time(rows: Sequence[Interaction]) -> float | None:
    times = [row.response_time_ms for row in rows if row.response_time_ms is not None]
    return sum(times) / len(times) if times else None


def extract_features(
    history: Sequence[Interaction], target_concept_id: str, prediction_timestamp_ms: int
) -> dict[str, float | int | None]:
    """Calculate the 12 historical features without using the target answer.

    Args:
        history: One learner's Interaction records, in any timestamp order.
            Repeated questions are valid; each response needs a unique event ID.
            A multi-concept response counts once overall and once for each skill.
        target_concept_id: Nonblank concept ID in the same namespace as history.
        prediction_timestamp_ms: Nonnegative integer exclusive cutoff in ms.
            Use answer-availability timestamps with a consistent time origin.

    Returns:
        A dictionary ordered exactly as FEATURE_NAMES. Durations and elapsed
        times are milliseconds; accuracies are fractions. Unknown statistics
        are None, while known counts and empty streaks are zero. Previous and
        overall statistics use all concepts; skill statistics use only the target.

    Raises:
        ValueError: Invalid target/cutoff, non-Interaction elements, mixed learners,
            or duplicate interaction IDs, including malformed future history.

    Input is not mutated. Stable timestamp sorting retains source order among
    equal-time prior attempts. All attempts at or after the cutoff are excluded;
    arbitrary IDs never serve as a guessed within-timestamp response order.
    Missing response durations occupy recent-window positions but are excluded
    from duration means. Recent windows use natural log and reach the 50-attempt
    cap at 148 previous skill attempts (147 yields 49), correcting PR #6's footnote.
    See P2/README.md for each feature definition and the unresolved tensor layout.
    """
    validate_identifier(target_concept_id, "target_concept_id")
    validate_milliseconds(prediction_timestamp_ms, "prediction_timestamp_ms")
    if any(not isinstance(row, Interaction) for row in history):
        raise ValueError("history must contain Interaction records")
    if len({row.learner_id for row in history}) > 1:
        raise ValueError("history must contain only one learner")
    if len({row.interaction_id for row in history}) != len(history):
        raise ValueError("history contains duplicate interaction_id values")
    # Strict inequality excludes the target answer even if supplied in history.
    # Stable sorting preserves source order among equal-time prior attempts.
    prior = sorted(
        (row for row in history if row.timestamp_ms < prediction_timestamp_ms),
        key=lambda row: row.timestamp_ms,
    )
    skill = [row for row in prior if target_concept_id in row.concept_ids]
    n = len(skill)
    # Natural log: the capped window first reaches 50 at n=148.
    recent_count = min(n, 50, floor(10 * log(n + 1)))
    recent = skill[-recent_count:] if recent_count else []
    streak = 0
    # Only target-skill attempts affect its streak, not intervening other skills.
    for row in reversed(skill):
        if not row.correct:
            break
        streak += 1
    previous = prior[-1] if prior else None
    # Literal insertion order mirrors FEATURE_NAMES. Unknown times/accuracies
    # remain None; only observed counts and an empty streak are known zeros.
    return {
        "previous_response_time": previous.response_time_ms if previous else None,
        "previous_correct": int(previous.correct) if previous else None,
        "time_since_previous_interaction": (
            prediction_timestamp_ms - previous.timestamp_ms if previous else None
        ),
        "time_since_last_skill_attempt": (
            prediction_timestamp_ms - skill[-1].timestamp_ms if skill else None
        ),
        "skill_attempt_count": n,
        "skill_avg_response_time": _mean_time(skill),
        "skill_accuracy": _accuracy(skill),
        "recent_skill_avg_response_time": _mean_time(recent),
        "recent_skill_accuracy": _accuracy(recent),
        "skill_correct_streak": streak,
        "overall_accuracy": _accuracy(prior),
        "overall_attempt_count": len(prior),
    }


@dataclass(frozen=True)
class FeatureVector:
    """Ordered raw values and observation mask, each with 12 entries.

    Attributes:
        values: Float values in FEATURE_NAMES order; missing entries contain 0.0.
        observed_mask: True for observed values, False for missing statistics.
            This distinguishes measured zero from unknown accuracy or duration.

    This is a feature mask, not a sequence-padding mask. Instances are returned
    by to_feature_vector; no tensor scaling or sequence packing is implied.
    """

    values: tuple[float, ...]
    observed_mask: tuple[bool, ...]


def to_feature_vector(features: Mapping[str, float | int | None]) -> FeatureVector:
    """Convert exactly the 12 named features into values and missingness mask.

    Args:
        features: Mapping containing exactly FEATURE_NAMES. Key order is ignored.
            Values must be finite real numbers or None. Boolean inputs are rejected.

    Returns:
        FeatureVector in deterministic FEATURE_NAMES order. None becomes a zero
        placeholder with mask False; measured zero has mask True. No scaling or
        statistical imputation is performed and the input mapping is not mutated.

    Raises:
        ValueError: Missing/extra keys or nonfinite/nonnumeric supplied values.
    """
    if set(features) != set(FEATURE_NAMES):
        raise ValueError("features must contain exactly FEATURE_NAMES")
    values = []
    mask = []
    for name in FEATURE_NAMES:
        value = features[name]
        if value is not None and (
            isinstance(value, bool) or not isinstance(value, Real) or not isfinite(value)
        ):
            raise ValueError(f"{name} must be a finite number or None")
        values.append(0.0 if value is None else float(value))
        mask.append(value is not None)
    return FeatureVector(tuple(values), tuple(mask))
