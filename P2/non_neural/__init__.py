"""Public P2 APIs; independent of the unmerged shared ORM and model code.

Use extract_features/to_feature_vector for model inputs, ConceptSelector for
rankings, and project_adapter.ControllerConceptSelector for the PR #7 facade.
"""
from .adaptive_selector import Selection, review_recency, select_concept
from .concept_selector import (
    CandidateConcept,
    ConceptSelection,
    ConceptSelector,
    PredictionError,
)
from .feature_extractor import (
    FEATURE_NAMES,
    FeatureVector,
    extract_features,
    to_feature_vector,
)
from .interfaces import (
    AttemptHistorySource,
    AttemptRepository,
    DatabaseAttemptRepository,
    ErrorPredictor,
    InMemoryAttemptRepository,
    MockErrorPredictor,
    PredictionRequest,
    SequenceErrorPredictor,
)
from .project_adapter import ControllerConceptSelector
from .question_validator import (
    Question,
    QuestionValidator,
    ValidationResult,
    validate_question,
)
from .schemas import Interaction

__all__ = [
    "Interaction", "FEATURE_NAMES", "FeatureVector", "extract_features",
    "to_feature_vector", "Selection", "select_concept", "review_recency",
    "CandidateConcept", "ConceptSelection", "ConceptSelector", "PredictionError",
    "AttemptRepository", "ErrorPredictor", "InMemoryAttemptRepository",
    "MockErrorPredictor", "PredictionRequest", "SequenceErrorPredictor",
    "AttemptHistorySource", "DatabaseAttemptRepository", "ControllerConceptSelector",
    "Question", "QuestionValidator", "ValidationResult", "validate_question",
]
