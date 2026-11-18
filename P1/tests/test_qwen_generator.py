"""Check question and choice generation with simulated model replies."""
import io
import json
from types import SimpleNamespace

import pytest

import qwen_generator
from qwen_generator import QwenQuestionGenerator


class MultipleChoiceQuestion:
    number_responses = 4


class ShortAnswerQuestion:
    pass


def question(kind=MultipleChoiceQuestion()):
    return SimpleNamespace(
        concept=SimpleNamespace(field=SimpleNamespace(name='Biology')),
        context_facts=[SimpleNamespace(
            value_str='Plants convert light energy to chemical energy '
                      'during photosynthesis.'
        )],
        answer_fact=SimpleNamespace(value_str='photosynthesis'),
        type=kind,
    )


def test_question_uses_pr7_data_and_rejects_answer_leak():
    generator = QwenQuestionGenerator()
    outputs = iter([
        'Is photosynthesis the answer?',
        'What process converts light energy to chemical energy in plants?',
    ])
    prompts = []

    def complete(prompt):
        prompts.append(prompt)
        return next(outputs)

    generator._complete = complete
    assert generator.get_question_text(question()) == (
        'What process converts light energy to chemical energy in plants?'
    )
    assert '"answer_fact": "photosynthesis"' in prompts[0]
    assert len(prompts) == 2


def test_distractors_and_short_answer():
    generator = QwenQuestionGenerator()
    generator._complete = lambda prompt: 'Respiration\nFermentation\nDigestion'
    assert generator.generate_distractors(question()) == [
        'Respiration', 'Fermentation', 'Digestion'
    ]
    assert generator.generate_distractors(question(ShortAnswerQuestion())) == []


def test_rejects_bad_distractors():
    generator = QwenQuestionGenerator()
    generator._complete = lambda prompt: 'photosynthesis\nRespiration\nRespiration'
    with pytest.raises(ValueError, match='distractors'):
        generator.generate_distractors(question())


def test_chat_request_uses_local_model(monkeypatch):
    def fake_urlopen(request, timeout):
        assert request.full_url == 'http://127.0.0.1:8080/v1/chat/completions'
        assert json.loads(request.data)['model'] == 'qwen3:8b-q4_K_M'
        assert timeout == 90
        return io.BytesIO(json.dumps({
            'choices': [{'message': {'content': 'What process is this?'}}]
        }).encode())

    monkeypatch.setattr(qwen_generator, 'urlopen', fake_urlopen)
    assert QwenQuestionGenerator()._complete('test') == 'What process is this?'
