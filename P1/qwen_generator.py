"""Ask a local Qwen server for study questions and answer choices."""
import json
from urllib.request import Request, urlopen


class QwenQuestionGenerator:
    """Generate text from the concept, facts, and known answer."""

    def __init__(
        self, host: str = "http://127.0.0.1:8080",
        model: str = "qwen3:8b-q4_K_M",
    ) -> None:
        self.host = host.rstrip("/")
        self.model = model

    def _complete(self, prompt: str) -> str:
        data = json.dumps({
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
            "max_tokens": 150,
        }).encode()
        request = Request(
            f"{self.host}/v1/chat/completions", data=data,
            headers={"Content-Type": "application/json"},
        )
        with urlopen(request, timeout=90) as response:
            result = json.load(response)
        return result["choices"][0]["message"]["content"].strip()

    @staticmethod
    def _question_data(question: object) -> tuple[str, list[str], str, str]:
        concept = question.concept.field.name
        facts = [fact.value_str for fact in question.context_facts]
        answer = question.answer_fact.value_str
        kind = type(question.type).__name__
        if kind not in ("MultipleChoiceQuestion", "ShortAnswerQuestion"):
            raise ValueError("unsupported question type")
        if not concept or not answer or not answer.strip():
            raise ValueError("concept and answer must contain text")
        if not facts or any(not fact or not fact.strip() for fact in facts):
            raise ValueError("context facts must contain text")
        return concept, facts, answer, kind

    def get_question_text(self, question: object) -> str:
        """Ask about the known answer without giving it away."""
        concept, facts, answer, kind = self._question_data(question)
        source = json.dumps({
            "concept": concept, "context_facts": facts, "answer_fact": answer,
        })
        question_type = (
            "multiple-choice" if kind == "MultipleChoiceQuestion" else "short-answer"
        )
        prompt = (
            "/no_think\n"
            f"Write one {question_type} study question from this concept data. "
            "Its expected answer is "
            "answer_fact. Use only the supplied facts. Ask for the answer itself, "
            "not a related fact. Do not reveal the answer in the question. "
            "Return only one grammatical question ending in ?. "
            "If this is impossible, return UNABLE.\n"
            f"{source}"
        )
        for _ in range(2):
            text = self._complete(prompt).strip()
            if (
                text.endswith("?") and "\n" not in text
                and answer.casefold() not in text.casefold()
            ):
                return text
        raise ValueError("model did not return a usable question")

    def generate_distractors(self, question: object) -> list[str]:
        """Ask for the wrong choices in a multiple-choice question."""
        concept, facts, answer, kind = self._question_data(question)
        if kind != "MultipleChoiceQuestion":
            return []
        count = question.type.number_responses - 1
        if count < 1:
            raise ValueError("multiple-choice questions need at least two options")
        source = json.dumps({
            "concept": concept, "context_facts": facts, "answer_fact": answer,
        })
        prompt = (
            "/no_think\n"
            f"Write {count} plausible but incorrect answer choices for this "
            "study question. Each choice must be different from answer_fact "
            "and from the other choices. Return one choice per line, with no "
            "numbers, bullets, or explanation.\n"
            f"{source}"
        )
        for _ in range(2):
            choices = [line.strip() for line in self._complete(prompt).splitlines()]
            normalized = [choice.casefold() for choice in choices]
            if (
                len(choices) == count and all(choices)
                and len(set(normalized)) == count
                and all(answer.casefold() not in choice for choice in normalized)
            ):
                return choices
        raise ValueError("model did not return usable distractors")
