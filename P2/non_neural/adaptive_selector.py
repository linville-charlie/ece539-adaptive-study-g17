"""Rule-based selection from externally supplied error probabilities."""
from collections.abc import Mapping
from dataclasses import dataclass
from math import expm1, isfinite, log
from numbers import Real
from .schemas import validate_identifier, validate_milliseconds

SEVEN_DAYS_MS = 7 * 24 * 60 * 60 * 1000


def _number(value: float, name: str, lower: float, upper: float) -> None:
    if isinstance(value, bool) or not isinstance(value, Real) or not isfinite(value) or not lower <= value <= upper:
        raise ValueError(f"{name} must be finite and in [{lower}, {upper}]")


@dataclass(frozen=True)
class Selection:
    """Standalone winner: concept_id metadata and priority score in [0, 1].

    score is a ranking priority, not a calibrated probability of error.
    """
    concept_id: str
    score: float


def select_concept(
    predicted_error_probabilities: Mapping[str, float],
    last_reviewed_ms: Mapping[str, int | None],
    prediction_timestamp_ms: int,
    *, alpha: float = 0.8, half_life_ms: float = SEVEN_DAYS_MS,
) -> Selection:
    """Select maximum weighted priority from externally supplied predictions.

    Args:
        predicted_error_probabilities: Candidate ID to finite error probability
            in [0, 1]. Keys define the candidate set; it must be nonempty.
        last_reviewed_ms: Candidate ID to last answer-availability timestamp.
            Missing keys or None indicate never reviewed; extra keys are ignored.
        prediction_timestamp_ms: Nonnegative exclusive prediction cutoff in ms.
        alpha: Probability weight in [0, 1]; recency weight is 1 - alpha.
        half_life_ms: Positive finite exponential-recency half-life, in ms.

    Returns:
        Selection with the maximum score; lexical concept ID breaks exact ties.

    Raises:
        ValueError: Invalid IDs, times, probabilities, configuration, or empty
            candidates. A review timestamp later than the cutoff is invalid.

    This retained helper does not fetch history or call a predictor. Use
    ConceptSelector when those responsibilities should be coordinated together.
    """
    validate_milliseconds(prediction_timestamp_ms, "prediction_timestamp_ms")
    _number(alpha, "alpha", 0, 1)
    _number(half_life_ms, "half_life_ms", 0, float("inf"))
    if half_life_ms == 0:
        raise ValueError("half_life_ms must be positive")
    if not predicted_error_probabilities:
        raise ValueError("at least one candidate concept is required")
    scores = []
    for concept_id, probability in predicted_error_probabilities.items():
        validate_identifier(concept_id, "concept_id")
        _number(probability, "predicted error probability", 0, 1)
        reviewed = last_reviewed_ms.get(concept_id)
        recency = review_recency(
            reviewed, prediction_timestamp_ms, half_life_ms=half_life_ms,
        )
        scores.append(Selection(concept_id, alpha * probability + (1 - alpha) * recency))
    return min(scores, key=lambda item: (-item.score, item.concept_id))


def review_recency(
    last_reviewed_ms: int | None, prediction_timestamp_ms: int,
    *, half_life_ms: float = SEVEN_DAYS_MS,
) -> float:
    """Return exponential review recency in [0, 1], with one for never reviewed.

    Args:
        last_reviewed_ms: Nonnegative last review timestamp in ms, or None.
        prediction_timestamp_ms: Nonnegative current cutoff in the same ms origin.
        half_life_ms: Positive finite duration; defaults to seven days.

    Returns:
        1 - exp(-ln(2) * elapsed / half_life). Thus immediate review gives zero,
        one half-life gives 0.5, and very old reviews approach one. None gives one.

    Raises:
        ValueError: Invalid times, a future review, or a nonpositive/nonfinite
            half-life. Numeric IDs and response durations are not timestamps here.
    """
    validate_milliseconds(prediction_timestamp_ms, "prediction_timestamp_ms")
    _number(half_life_ms, "half_life_ms", 0, float("inf"))
    if half_life_ms == 0:
        raise ValueError("half_life_ms must be positive")
    if last_reviewed_ms is None:
        return 1.0
    validate_milliseconds(last_reviewed_ms, "last_reviewed_ms")
    if last_reviewed_ms > prediction_timestamp_ms:
        raise ValueError("last review cannot be in the future")
    elapsed = prediction_timestamp_ms - last_reviewed_ms
    return -expm1(-log(2) * (elapsed / half_life_ms))
