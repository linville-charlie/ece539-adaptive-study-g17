"""Thin bridge to PR #7's proposed select_concept(...)->Concept method.

The actual ConceptEvaluationData class is empty and database lookup signatures
are unfinished. Explicit callbacks avoid guessing its future fields or importing
unmerged/broken ORM models. This is a facade over the existing selector, not a
second ranking algorithm or a replacement QuestionController.
"""
from collections.abc import Callable, Sequence
from typing import Generic, TypeVar

from .concept_selector import CandidateConcept, ConceptSelection, ConceptSelector
from .schemas import validate_identifier

EvaluationT = TypeVar("EvaluationT")
ConceptT = TypeVar("ConceptT")


class ControllerConceptSelector(Generic[EvaluationT, ConceptT]):
    """Adapt the team's selector method shape while returning its own Concept type.

    The local app may create one adapter per learner/session, matching the PR
    discussion's per-instance database design. No shared model is monkey-patched.
    All identity conversion is explicit and belongs to the integration layer.
    """

    def __init__(
        self, selector: ConceptSelector, *, learner_id: str,
        to_candidate: Callable[[EvaluationT], CandidateConcept],
        get_concept_by_id: Callable[[str], ConceptT],
        prediction_clock_ms: Callable[[], int],
    ) -> None:
        """Bind the core service to the controller's metadata and lookup contracts.

        Args:
            selector: P2 service with injected repository and predictor.
            learner_id: Nonblank session identity used for history isolation.
            to_candidate: Map a project's ConceptEvaluationData to P2 metadata.
            get_concept_by_id: Resolve a selected string ID to the project's
                Concept object. Wrap/convert ORM integer IDs in this callback.
            prediction_clock_ms: Return a cutoff in the same millisecond origin
                as stored attempts. Called once per select_concept invocation.

        Raises:
            ValueError: Empty learner identity. Other callbacks are evaluated
                only when selecting; their failures propagate to the controller.
        """
        validate_identifier(learner_id, "learner_id")
        self.selector = selector
        self.learner_id = learner_id
        self.to_candidate = to_candidate
        self.get_concept_by_id = get_concept_by_id
        self.prediction_clock_ms = prediction_clock_ms
        self.last_selection: ConceptSelection | None = None

    def select_concept(self, concept_eval_data: Sequence[EvaluationT]) -> ConceptT:
        """Select and return the project's Concept using the PR's method name.

        Args:
            concept_eval_data: Eligible project-specific evaluation records.
                Their final attributes are intentionally not assumed here.

        Returns:
            The object returned by get_concept_by_id for the winning concept ID.
            last_selection retains scoring details after a successful lookup.

        Raises:
            ValueError, PredictionError: As documented by the core selector.
            Exception: Metadata mapping, clock, repository, and lookup failures
                propagate unchanged. last_selection is cleared before each call
                so a failed selection cannot expose a stale successful result.
        """
        self.last_selection = None
        candidates = [self.to_candidate(item) for item in concept_eval_data]
        result = self.selector.select_next_concept(
            self.learner_id, candidates, self.prediction_clock_ms(),
        )
        concept = self.get_concept_by_id(result.concept_id)
        self.last_selection = result
        return concept
