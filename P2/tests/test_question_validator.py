from dataclasses import replace
import pytest
from non_neural import Question, validate_question

BASE = Question('q', ('a', 'b'), 'math', 'What is 2 + 2?', ('3', '4'), '4')


def test_valid():
    assert validate_question(BASE) is None
    assert validate_question(replace(BASE, answer_options=(' New York ', 'Paris'), correct_answer='new  YORK')) is None


@pytest.mark.parametrize('changes, message', [
    ({'question_text': ' '}, 'question_text'),
    ({'answer_options': ('4', ' 4 ')}, 'duplicate'),
    ({'answer_options': ('Four', 'FOUR')}, 'duplicate'),
    ({'answer_options': ('4',)}, 'at least two'),
    ({'answer_options': ('4', '')}, 'answer option'),
    ({'correct_answer': ''}, 'correct_answer'),
    ({'correct_answer': None}, 'correct_answer'),
    ({'correct_answer': '5'}, 'exactly one'),
    ({'concept_ids': ()}, 'concept_ids'),
    ({'concept_ids': ('',)}, 'concept_id'),
    ({'question_id': ''}, 'question_id'),
    ({'subject_id': ''}, 'subject_id'),
    ({'explanation': 42}, 'explanation'),
])
def test_invalid(changes, message):
    with pytest.raises(ValueError, match=message):
        validate_question(replace(BASE, **changes))


def test_structured_mapping_with_lists():
    from dataclasses import asdict
    from non_neural import QuestionValidator
    question = asdict(BASE)
    question['concept_ids'] = ['a', 'b']
    question['answer_options'] = ['3', '4']
    result = QuestionValidator().validate(question)
    assert result.is_valid
    assert result.errors == ()
    assert result.question.question_id == 'q'


@pytest.mark.parametrize('changes', [
    {'question_text': ''}, {'concept_ids': []}, {'subject_id': ''},
    {'answer_options': ['4', ' 4 ']}, {'correct_answer': None}, {'correct_answer': '5'},
])
def test_structured_invalid_result(changes):
    from non_neural import QuestionValidator
    result = QuestionValidator().validate(replace(BASE, **changes))
    assert not result.is_valid
    assert result.errors and isinstance(result.errors[0], str)
    assert result.question is None


def test_configured_minimum_options():
    from non_neural import QuestionValidator
    validator = QuestionValidator(min_options=3)
    assert not validator.validate(BASE).is_valid
    assert validator.validate(replace(BASE, answer_options=['2', '3', '4'])).is_valid


@pytest.mark.parametrize('minimum', [0, 1, True, 2.5])
def test_invalid_option_configuration(minimum):
    from non_neural import QuestionValidator
    with pytest.raises(ValueError):
        QuestionValidator(min_options=minimum)


@pytest.mark.parametrize('question', [{}, {'extra': 'field'}, None, 'raw generated text'])
def test_invalid_question_shape_returns_error(question):
    from non_neural import QuestionValidator
    result = QuestionValidator().validate(question)
    assert not result.is_valid
    assert result.errors
