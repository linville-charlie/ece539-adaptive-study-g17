"""Structural checks only: these checks do not establish factual correctness."""
from collections.abc import Mapping
from dataclasses import dataclass
from .schemas import validate_concepts, validate_identifier


def _normalize(text: str) -> str:
    return " ".join(text.split()).casefold()


@dataclass(frozen=True)
class Question:
    """Generated multiple-choice candidate; validate before presenting to learners."""
    question_id: str
    concept_ids: tuple[str, ...] | list[str]
    subject_id: str
    question_text: str
    answer_options: tuple[str, ...] | list[str]
    correct_answer: str
    explanation: str | None = None

    def __post_init__(self) -> None:
        # Copy JSON-style lists without validating generated candidate content.
        for name in ("concept_ids", "answer_options"):
            value = getattr(self, name)
            if isinstance(value, list):
                object.__setattr__(self, name, tuple(value))


def validate_question(question: Question, *, min_options: int = 2) -> None:
    """Raise ValueError on malformed structure, otherwise return None.

    Answer matching collapses whitespace and ignores case; punctuation stays
    significant. The optional explanation is not fact checked.
    """
    if type(min_options) is not int or min_options < 2:
        raise ValueError("min_options must be an integer of at least two")
    validate_identifier(question.question_id, "question_id")
    validate_identifier(question.subject_id, "subject_id")
    concepts = tuple(question.concept_ids) if isinstance(question.concept_ids, list) else question.concept_ids
    validate_concepts(concepts)
    validate_identifier(question.question_text, "question_text")
    if not isinstance(question.answer_options, (tuple, list)) or len(question.answer_options) < min_options:
        raise ValueError(f"answer_options must contain at least two options (configured minimum: {min_options})")
    for option in question.answer_options:
        validate_identifier(option, "answer option")
    options = [_normalize(option) for option in question.answer_options]
    if len(set(options)) != len(options):
        raise ValueError("duplicate answer options after normalization")
    validate_identifier(question.correct_answer, "correct_answer")
    if options.count(_normalize(question.correct_answer)) != 1:
        raise ValueError("correct_answer must match exactly one answer option")
    if question.explanation is not None and not isinstance(question.explanation, str):
        raise ValueError("explanation must be a string or None")


@dataclass(frozen=True)
class ValidationResult:
    """Structural acceptance and errors; never a factual correctness verdict.

    The current validator reports the first error. An accepted question is
    available for callers that supplied a mapping and need the parsed record.
    """

    is_valid: bool
    errors: tuple[str, ...] = ()
    question: Question | None = None


class QuestionValidator:
    """Generator-independent structured validation for records or mappings."""

    def __init__(self, *, min_options: int = 2) -> None:
        if type(min_options) is not int or min_options < 2:
            raise ValueError("min_options must be an integer of at least two")
        self.min_options = min_options

    def validate(self, question: Question | Mapping[str, object]) -> ValidationResult:
        """Return acceptance or the first clear structural error without raising.

        Invalid validator configuration raises at construction. Dictionary keys
        must match Question fields; absent required or extra fields are errors.
        Text/list normalization is used only for checking, not rewriting content.
        """
        if isinstance(question, Mapping):
            try:
                question = Question(**question)
            except TypeError as error:
                return ValidationResult(False, (f"invalid question fields: {error}",))
        if not isinstance(question, Question):
            return ValidationResult(False, ("question must be a Question or mapping",))
        try:
            validate_question(question, min_options=self.min_options)
        except ValueError as error:
            return ValidationResult(False, (str(error),))
        return ValidationResult(True, question=question)
