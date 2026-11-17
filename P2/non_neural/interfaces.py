"""Dependency boundaries for history storage and error prediction.

These protocols do not import SQLAlchemy, PyTorch, or unmerged project code.
A shared SQLite adapter can implement them structurally, without inheritance.
All timestamps and durations crossing this boundary are milliseconds.
"""
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Protocol

from .feature_extractor import FeatureVector
from .schemas import Interaction, validate_identifier, validate_milliseconds


class AttemptRepository(Protocol):
    """Read one learner's answered attempts, independent of their storage format."""

    def get_history(
        self, learner_id: str, before_timestamp_ms: int | None = None,
    ) -> list[Interaction]:
        """Return chronological attempts for learner_id before an optional cutoff.

        Args:
            learner_id: Nonblank learner identifier, including for local sessions.
            before_timestamp_ms: Exclusive answer-availability cutoff, or None
                to retrieve all attempts. Use a consistent millisecond origin.

        Returns:
            One Interaction per response event, including all concept associations.
            Equal-time records must retain a known source order when available.

        Raises:
            ValueError: If query identifiers or timestamps are invalid.
            Exception: Storage errors should propagate rather than imply no history.
        """
        ...


class AttemptHistorySource(Protocol):
    """Proposed minimal method for the shared DatabaseController to implement.

    PR #7 does not yet define this method or a persistent attempt model. This
    protocol documents an integration requirement, not an existing ORM API.
    """

    def get_attempt_history(
        self, learner_id: str, before_timestamp_ms: int | None = None,
    ) -> list[Interaction]:
        """Return attempts using the same contract as AttemptRepository.get_history.

        The shared implementation owns SQL queries, identifier conversion, and
        grouping of concept joins. It must raise on storage errors.
        """
        ...


class DatabaseAttemptRepository:
    """Translate the proposed database method name to P2's repository protocol.

    Args:
        source: Shared controller implementing get_attempt_history. No connection,
            tables, migrations, SQL, or persistence are created by this adapter.
    """

    def __init__(self, source: AttemptHistorySource) -> None:
        """Retain the injected history source without opening a database."""
        self.source = source

    def get_history(
        self, learner_id: str, before_timestamp_ms: int | None = None,
    ) -> list[Interaction]:
        """Delegate an exclusive millisecond query; propagate source exceptions."""
        validate_identifier(learner_id, "learner_id")
        if before_timestamp_ms is not None:
            validate_milliseconds(before_timestamp_ms, "before_timestamp_ms")
        return self.source.get_attempt_history(learner_id, before_timestamp_ms)


class ErrorPredictor(Protocol):
    """Legacy target-row predictor interface; returns probability of an error.

    Use SequenceErrorPredictor when inference requires chronological context.
    This interface does not prescribe the team's eventual neural tensor layout.
    """

    def predict_error(
        self, learner_id: str, concept_id: str, subject_id: str,
        features: dict[str, float | int | None],
    ) -> float:
        """Return a finite probability in [0, 1], with 1 meaning certain error.

        IDs are metadata. Features contain the agreed 12 historical values in
        FEATURE_NAMES order, with None for unknown statistics and times in ms.
        Implementations may raise inference exceptions; the selector applies its
        configured failure policy and validates the returned probability.
        """
        ...


@dataclass(frozen=True)
class PredictionRequest:
    """Leakage-safe context supplied to a sequence-aware predictor adapter.

    Attributes:
        learner_id: Learner grouping identifier, not a continuous model feature.
        concept_id: Target concept metadata in the shared global namespace.
        subject_id: Metadata for subject routing; not a numeric measurement.
        prediction_timestamp_ms: Exclusive cutoff for this prediction, in ms.
        history: Immutable chronological prior attempts for this learner only.
            Every timestamp is strictly below the cutoff. Equal timestamps retain
            repository source order. This is raw history, not a padded tensor.
        features: Read-only mapping of the 12 target-context historical features.
        feature_vector: The same values plus their observation mask, in fixed order.

    The selector constructs requests; it does not supply a target answer, target
    duration, or submitted answer. The neural adapter still owns sequence feature
    construction, scaling, padding, and sequence masks. It must compute historical
    sequence rows at their own cutoffs to avoid within-sequence label leakage.
    """

    learner_id: str
    concept_id: str
    subject_id: str
    prediction_timestamp_ms: int
    history: tuple[Interaction, ...]
    features: Mapping[str, float | int | None]
    feature_vector: FeatureVector


class SequenceErrorPredictor(Protocol):
    """Predict from contextual input without forcing the model to use a flat row."""

    def predict_error(self, request: PredictionRequest) -> float:
        """Return finite error probability in [0, 1], or raise on inference failure.

        request contains cutoff-filtered history, target metadata, historical
        statistics, and an observation mask. It intentionally leaves the final
        tensor layout to the neural teammate. No neural inference is implemented
        by the protocol itself.
        """
        ...


class InMemoryAttemptRepository:
    """Synthetic-data repository with no persistence.

    Args:
        attempts: Optional initial Interaction records, in any timestamp order.

    Raises:
        ValueError: For non-Interaction values or duplicate interaction IDs.

    Event IDs must be globally unique within this adapter, including across
    learners. A repeated question is allowed when it has a new interaction ID.
    Returned lists are copies; their Interaction records are immutable.
    """

    def __init__(self, attempts: Iterable[Interaction] = ()) -> None:
        """Copy validated initial attempts; no database or external files are used."""
        self._attempts: list[Interaction] = []
        self._ids: set[str] = set()
        for attempt in attempts:
            self.add(attempt)

    def add(self, attempt: Interaction) -> None:
        """Store one immutable attempt; raise ValueError for invalid/duplicate IDs."""
        if not isinstance(attempt, Interaction):
            raise ValueError("attempt must be an Interaction")
        if attempt.interaction_id in self._ids:
            raise ValueError("duplicate interaction_id")
        self._attempts.append(attempt)
        self._ids.add(attempt.interaction_id)

    def get_history(
        self, learner_id: str, before_timestamp_ms: int | None = None,
    ) -> list[Interaction]:
        """Return a sorted copy for one learner with an exclusive ms cutoff.

        See AttemptRepository.get_history for parameter and error contracts.
        Stable sorting retains insertion order among prior equal-time attempts.
        An unknown learner returns an empty list, not invented statistics.
        """
        validate_identifier(learner_id, "learner_id")
        if before_timestamp_ms is not None:
            validate_milliseconds(before_timestamp_ms, "before_timestamp_ms")
        return sorted(
            (attempt for attempt in self._attempts
             if attempt.learner_id == learner_id
             and (before_timestamp_ms is None
                  or attempt.timestamp_ms < before_timestamp_ms)),
            key=lambda attempt: attempt.timestamp_ms,
        )


class MockErrorPredictor:
    """Deterministic lookup fixture, not an estimator or a trained model.

    Args:
        probabilities: Values keyed by (subject_id, concept_id), copied on input.
            Probability validation is deliberately left to the selector so tests
            can exercise malformed model responses. Missing keys raise KeyError.
    """

    def __init__(self, probabilities: Mapping[tuple[str, str], float]) -> None:
        """Copy test probabilities; never load model weights or neural libraries."""
        self._probabilities = dict(probabilities)

    def predict_error(
        self, learner_id: str, concept_id: str, subject_id: str,
        features: dict[str, float | int | None],
    ) -> float:
        """Return the configured value for subject/concept; raise KeyError if absent.

        learner_id and features follow ErrorPredictor's contract but do not affect
        this synthetic lookup. Its outputs must not be reported as real inference.
        """
        return self._probabilities[(subject_id, concept_id)]
