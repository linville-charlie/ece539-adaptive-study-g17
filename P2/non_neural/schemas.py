"""Shared immutable records; identifiers are metadata, not continuous features."""
from dataclasses import dataclass


def validate_identifier(value: str, name: str) -> None:
    """Validate one identifier without changing its spelling.

    Args:
        value: Expected nonblank string; numeric source IDs need preprocessing.
        name: Human-readable field name used in the error message.

    Returns:
        None when valid. Case and surrounding whitespace are preserved.

    Raises:
        ValueError: If value is not a string or contains only whitespace.
    """
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a nonempty string")


def validate_concepts(values: tuple[str, ...]) -> None:
    """Validate a nonempty immutable concept association, returning None.

    Args:
        values: Tuple of distinct nonblank string concept IDs. The Interaction
            constructor converts input lists before calling this helper.

    Raises:
        ValueError: An association is empty, duplicated, or contains invalid IDs.
    """
    if not isinstance(values, tuple) or not values:
        raise ValueError("concept_ids must be a nonempty tuple")
    for value in values:
        validate_identifier(value, "concept_id")
    if len(set(values)) != len(values):
        raise ValueError("concept_ids must be distinct")


def validate_milliseconds(value: int, name: str) -> None:
    """Validate a nonnegative integer millisecond value, returning None.

    Args:
        value: Timestamp or duration in milliseconds; bool is not accepted.
        name: Field name included in any validation error.

    Raises:
        ValueError: Negative, fractional, boolean, or non-integer input.
    """
    if type(value) is not int or value < 0:
        raise ValueError(f"{name} must be a nonnegative integer in milliseconds")


@dataclass(frozen=True)
class Interaction:
    """One answered question after dataset preprocessing.

    Args:
        learner_id: Nonblank learner grouping identifier.
        interaction_id: Nonblank unique response-event identifier, not a question ID.
        question_id: Nonblank identifier of the question answered.
        concept_ids: Nonempty list or tuple of distinct nonblank skill identifiers.
            Lists are copied into tuples; multiple concepts are preserved.
        subject_id: Nonblank subject metadata for eventual model-head routing.
        timestamp_ms: Nonnegative integer answer-availability timestamp in ms.
        response_time_ms: Nonnegative integer answer duration in ms, or None.
        correct: Observed correctness as a Python bool, not an integer or string.

    Raises:
        ValueError: An identifier, concept association, time, or correctness value
            is invalid. Missing required constructor fields raise TypeError.

    IDs are metadata, never continuous numerical features. A multi-concept
    response counts once overall and once per associated concept. Global event-ID
    uniqueness belongs to the repository; the extractor checks within a history.
    """

    learner_id: str
    interaction_id: str
    question_id: str
    concept_ids: tuple[str, ...] | list[str]
    subject_id: str
    timestamp_ms: int
    response_time_ms: int | None
    correct: bool

    def __post_init__(self) -> None:
        for name in ("learner_id", "interaction_id", "question_id", "subject_id"):
            validate_identifier(getattr(self, name), name)
        # Accept JSON-style lists while retaining an immutable internal record.
        if isinstance(self.concept_ids, list):
            object.__setattr__(self, "concept_ids", tuple(self.concept_ids))
        validate_concepts(self.concept_ids)
        validate_milliseconds(self.timestamp_ms, "timestamp_ms")
        if self.response_time_ms is not None:
            validate_milliseconds(self.response_time_ms, "response_time_ms")
        if type(self.correct) is not bool:
            raise ValueError("correct must be a bool")
