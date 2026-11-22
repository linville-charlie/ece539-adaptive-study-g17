#   539g17 Adaptive Study Integration Project
#   Copyright (C) 2026  A. Kancherla, C. Linville, Q. Schultz, E. Wulf.
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as published
#   by the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# Authors of this file:
#
# - Charlie Linville
#
# This file header was last modified 21 Nov 2026.
"""Check short-answer generation with simulated model replies."""

import io
import json
from types import SimpleNamespace
from urllib.request import Request

import pytest

from ece539_adaptive_study_g17.questions import qwen_generator
from ece539_adaptive_study_g17.questions.qwen_generator import QwenQuestionGenerator


class ShortAnswerQuestion:
    pass


def question(kind: object | None = None) -> SimpleNamespace:
    if kind is None:
        kind = ShortAnswerQuestion()
    return SimpleNamespace(
        concept=SimpleNamespace(field=SimpleNamespace(name="Biology")),
        context_facts=[
            SimpleNamespace(
                value_str="Plants convert light energy to chemical energy "
                "during photosynthesis.",
                field_column=SimpleNamespace(name="description"),
            )
        ],
        answer_fact=SimpleNamespace(
            value_str="photosynthesis",
            field_column=SimpleNamespace(name="process"),
        ),
        type=kind,
    )


def test_question_uses_facts_and_rejects_answer_leak() -> None:
    generator = QwenQuestionGenerator()
    outputs = iter(
        [
            "Is photosynthesis the answer?",
            "What process converts light energy to chemical energy in plants?",
        ]
    )
    prompts = []

    def complete(prompt: str) -> str:
        prompts.append(prompt)
        return next(outputs)

    generator._complete = complete
    assert generator.get_question_text(question()) == (
        "What process converts light energy to chemical energy in plants?"
    )
    assert '"value": "photosynthesis"' in prompts[0]
    assert '"column": "process"' in prompts[0]
    assert "short-answer" in prompts[0]
    expected_attempts = 2
    assert len(prompts) == expected_attempts


def test_short_answer_can_be_a_single_letter() -> None:
    generator = QwenQuestionGenerator()
    generator._complete = lambda prompt: "What grade does the top tier receive?"
    data = question()
    data.answer_fact.value_str = "A"
    data.context_facts[0].value_str = "The top tier receives grade A."
    assert generator.get_question_text(data) == "What grade does the top tier receive?"


def test_rejects_other_question_types() -> None:
    generator = QwenQuestionGenerator()
    with pytest.raises(ValueError, match="type"):
        generator.get_question_text(question(object()))


def test_chat_request_uses_local_model(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_urlopen(request: Request, timeout: int) -> io.BytesIO:
        assert request.full_url == "http://127.0.0.1:8080/v1/chat/completions"
        assert json.loads(request.data)["model"] == "qwen3:8b-q4_K_M"
        expected_timeout = 90
        assert timeout == expected_timeout
        return io.BytesIO(
            json.dumps(
                {"choices": [{"message": {"content": "What process is this?"}}]}
            ).encode()
        )

    monkeypatch.setattr(qwen_generator, "urlopen", fake_urlopen)
    assert QwenQuestionGenerator()._complete("test") == "What process is this?"
