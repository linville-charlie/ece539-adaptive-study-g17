"""Adaptive selection service behind the team's proposed selector facade.

No ORM, controller, UI, or generator is imported. project_adapter.py maps the
unmerged PR #7 facade's select_concept method to this independently tested core.
"""
from collections.abc import Sequence
from dataclasses import dataclass
from types import MappingProxyType

from .adaptive_selector import SEVEN_DAYS_MS, _number, review_recency
from .feature_extractor import extract_features, to_feature_vector
from .interfaces import (
    AttemptRepository, ErrorPredictor, PredictionRequest, SequenceErrorPredictor,
)
from .schemas import Interaction, validate_identifier, validate_milliseconds


@dataclass(frozen=True)
class CandidateConcept:
    """Eligible concept identity; no learner accuracy is stored on the concept.

    Args:
        concept_id: Nonblank globally namespaced string. Dataset integer IDs must
            be mapped consistently by the source adapter, not treated as floats.
        subject_id: Nonblank subject metadata for future neural head routing.

    Raises:
        ValueError: If either identifier is invalid. Repeated candidates are
            rejected by the selector rather than silently deduplicated.
    """

    concept_id: str
    subject_id: str

    def __post_init__(self) -> None:
        """Validate metadata without guessing a subject from the concept ID."""
        validate_identifier(self.concept_id, "concept_id")
        validate_identifier(self.subject_id, "subject_id")


@dataclass(frozen=True)
class ConceptSelection:
    """One candidate's priority breakdown, usable for a winner or full ranking.

    concept_id and subject_id identify the candidate. predicted_error_probability,
    recency_score, and selection_score are in [0, 1]. The combined score is a
    priority, not a calibrated probability. used_fallback means an inference
    exception was replaced by the explicitly configured fixed probability.
    """

    concept_id: str
    subject_id: str
    predicted_error_probability: float
    recency_score: float
    selection_score: float
    used_fallback: bool = False


class PredictionError(RuntimeError):
    """Candidate inference failed; inspect __cause__ for the original exception."""


class ConceptSelector:
    """Retrieve history, obtain predictions, and rank review candidates.

    Inject one of predictor (legacy row API) or sequence_predictor (context API).
    The ranking algorithm and failure policy are identical for both interfaces.
    For cold starts, unknown feature statistics remain None and recency is one.
    Predictors must support those values or raise; no mastery value is invented.
    """

    def __init__(
        self, repository: AttemptRepository, predictor: ErrorPredictor | None = None,
        *, sequence_predictor: SequenceErrorPredictor | None = None,
        alpha: float = 0.8, half_life_ms: float = SEVEN_DAYS_MS,
        fallback_error_probability: float | None = None,
    ) -> None:
        """Configure external dependencies and experimental scoring parameters.

        Args:
            repository: Source of learner-specific Interaction records.
            predictor: Optional row-based error predictor; mutually exclusive with
                sequence_predictor. Existing P2 positional calls remain supported.
            sequence_predictor: Optional context-aware error predictor receiving
                chronological raw history and masks through PredictionRequest.
            alpha: Probability weight in [0, 1], initially 0.8 (experimental).
            half_life_ms: Positive finite review-recency half-life in milliseconds.
            fallback_error_probability: None means fail on inference exceptions.
                A finite [0, 1] value explicitly enables fixed-probability fallback.

        Raises:
            ValueError: Invalid configuration, or neither/both predictor options.

        Repository failures and invalid returned probabilities always propagate;
        fallback only handles exceptions raised during predictor invocation.
        """
        if (predictor is None) == (sequence_predictor is None):
            raise ValueError("supply exactly one predictor or sequence_predictor")
        _number(alpha, "alpha", 0, 1)
        _number(half_life_ms, "half_life_ms", 0, float("inf"))
        if half_life_ms == 0:
            raise ValueError("half_life_ms must be positive")
        if fallback_error_probability is not None:
            _number(fallback_error_probability, "fallback_error_probability", 0, 1)
        self.repository = repository
        self.predictor = predictor
        self.sequence_predictor = sequence_predictor
        self.alpha = alpha
        self.half_life_ms = half_life_ms
        self.fallback_error_probability = fallback_error_probability

    def select_next_concept(
        self, learner_id: str, candidate_concepts: Sequence[CandidateConcept],
        prediction_timestamp_ms: int,
    ) -> ConceptSelection:
        """Return the highest-priority candidate using rank_concepts' contracts.

        Args:
            learner_id: Learner whose historical responses determine statistics.
            candidate_concepts: Nonempty eligible concepts with distinct IDs.
            prediction_timestamp_ms: Exclusive history cutoff in milliseconds.

        Returns:
            The first result of the deterministic ranking, with score components.

        Raises:
            ValueError: Invalid candidates, history, cutoff, or probabilities.
            PredictionError: Predictor failure without an enabled fallback.
            Exception: Repository failures propagate without conversion.
        """
        return self.rank_concepts(
            learner_id, candidate_concepts, prediction_timestamp_ms,
        )[0]

    def rank_concepts(
        self, learner_id: str, candidate_concepts: Sequence[CandidateConcept],
        prediction_timestamp_ms: int,
    ) -> list[ConceptSelection]:
        """Return all candidates by descending score, then lexical concept ID.

        Args:
            learner_id: Nonblank learner key, including a local session identity.
            candidate_concepts: Eligible CandidateConcept records. Duplicate IDs
                across any subjects are rejected; globally namespace IDs first.
            prediction_timestamp_ms: Nonnegative integer cutoff in milliseconds.

        Returns:
            One detailed result per candidate, with scores and fallback flags.
            Each invocation fetches history once and predicts once per candidate,
            in lexical ID order. Calling select_next_concept again reruns inference.

        Raises:
            ValueError: Empty/invalid candidates, malformed or mixed-learner
                history, duplicate attempt IDs, or invalid returned probabilities.
            PredictionError: Inference raised and no fallback was configured.
            Exception: Repository failures propagate. No partial ranking is returned.

        Defense in depth: current/future rows are removed even if the repository
        fails to apply its cutoff. Equal-time prior rows retain source order; all
        rows at the cutoff are excluded from features AND predictor history.
        """
        validate_identifier(learner_id, "learner_id")
        validate_milliseconds(prediction_timestamp_ms, "prediction_timestamp_ms")
        if not candidate_concepts:
            raise ValueError("at least one candidate concept is required")
        seen = set()
        for concept in candidate_concepts:
            if not isinstance(concept, CandidateConcept):
                raise ValueError("candidate_concepts must contain CandidateConcept records")
            if concept.concept_id in seen:
                raise ValueError("repeated concept_id; use globally namespaced IDs")
            seen.add(concept.concept_id)
        history = self.repository.get_history(learner_id, prediction_timestamp_ms)
        if any(not isinstance(attempt, Interaction) for attempt in history):
            raise ValueError("repository history must contain Interaction records")
        if any(attempt.learner_id != learner_id for attempt in history):
            raise ValueError("repository returned history for a different learner")
        if len({attempt.interaction_id for attempt in history}) != len(history):
            raise ValueError("history contains duplicate interaction_id values")
        prior = tuple(sorted(
            (attempt for attempt in history
             if attempt.timestamp_ms < prediction_timestamp_ms),
            key=lambda attempt: attempt.timestamp_ms,
        ))
        results = []
        for concept in sorted(candidate_concepts, key=lambda item: item.concept_id):
            features = extract_features(prior, concept.concept_id, prediction_timestamp_ms)
            # Compute recency before invoking external code; a legacy predictor
            # may mutate its private feature dictionary without changing ranking.
            elapsed = features["time_since_last_skill_attempt"]
            reviewed = None if elapsed is None else prediction_timestamp_ms - int(elapsed)
            recency = review_recency(
                reviewed, prediction_timestamp_ms, half_life_ms=self.half_life_ms,
            )
            request = PredictionRequest(
                learner_id, concept.concept_id, concept.subject_id,
                prediction_timestamp_ms, prior, MappingProxyType(features),
                to_feature_vector(features),
            )
            probability, used_fallback = self._predict(request)
            score = self.alpha * probability + (1 - self.alpha) * recency
            results.append(ConceptSelection(
                concept.concept_id, concept.subject_id, probability, recency,
                score, used_fallback,
            ))
        return sorted(results, key=lambda item: (-item.selection_score, item.concept_id))

    def _predict(self, request: PredictionRequest) -> tuple[float, bool]:
        """Apply the same inference failure policy to either injected model API."""
        used_fallback = False
        try:
            if self.sequence_predictor is not None:
                probability = self.sequence_predictor.predict_error(request)
            else:
                assert self.predictor is not None  # Enforced by construction.
                probability = self.predictor.predict_error(
                    request.learner_id, request.concept_id, request.subject_id,
                    dict(request.features),
                )
        except Exception as error:
            if self.fallback_error_probability is None:
                raise PredictionError(
                    f"prediction failed for {request.concept_id}",
                ) from error
            probability = self.fallback_error_probability
            used_fallback = True
        # Outside the exception handler: malformed model outputs never become
        # silent fallback predictions, even when an inference fallback is enabled.
        _number(probability, "predicted error probability", 0, 1)
        return probability, used_fallback
