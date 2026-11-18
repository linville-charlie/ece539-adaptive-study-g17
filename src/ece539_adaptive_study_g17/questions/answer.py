"""A user's answer to a question."""

from typing import Protocol

from ece539_adaptive_study_g17.questions.question import (
    MultipleChoiceQuestion,
    Question,
    ShortAnswerQuestion,
)


class Answer(Protocol):
    """A user's answer to a question."""

    def question(self) -> Question:
        """Get the question this answer is for."""
        ...

    def payload(self) -> str:
        """Get a consistent representation of an answer."""
        ...


class MultipleChoiceAnswer(Answer):
    """The answer to a multiple choice question."""

    # TODO determine if multiple-choice should have UI buttons or have the same
    # text-based interface as short answer, just with n options provided.
    # Right now, it's spec'd out to be its own UI component.
    def __init__(self, question: MultipleChoiceQuestion, answer: int) -> None:
        """Create a new multiple choice answer."""
        raise NotImplementedError  # TODO

    # TODO Implement protocol methods.


class ShortAnswerAnswer(Answer):
    """The answer to a multiple choice question."""

    def __init__(self, question: ShortAnswerQuestion, answer: int) -> None:
        """Create a new multiple choice answer."""
        raise NotImplementedError  # TODO

    # TODO Implement protocol methods.
