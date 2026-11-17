# One practice cycle

This walkthrough connects the implemented interfaces using synthetic history,
placeholder model probabilities, and a manually authored question. It does not run
an LSTM or FLAN-T5-small. See the [API reference](API.md) for contracts and the
[README](../README.md) for setup and proposed architecture changes.

## Executable pipeline

The controller-facing demonstration includes dependency injection, masked vectors,
three candidates across two subjects, full rankings, and winner selection:

```sh
PYTHONPATH=P2 P2/.venv/bin/python P2/examples/demo_pipeline.py
```

It uses InMemoryAttemptRepository, MockErrorPredictor, and ConceptSelector. Its
ranking is algebra (0.640000229), never-reviewed capitals (0.600000000), then
fractions (0.240000229). The selected algebra score is approximately 0.640000229.
All probabilities are mocked. The lower-level example also exercises the retained
question-validation helper from the earlier P2 task. The lower-level example below demonstrates
the retained functional helpers and how later responses change historical features.

## Run the lower-level example

From the repository root, start Python with:

```sh
PYTHONPATH=P2 P2/.venv/bin/python
```

Paste the following code:

```python
from non_neural import (
    FEATURE_NAMES,
    Interaction,
    Question,
    extract_features,
    select_concept,
    validate_question,
)

history = [
    Interaction('learner-1', 'i1', 'q1', ('algebra',), 'math', 1000, 4000, False),
    Interaction('learner-1', 'i2', 'q2', ('algebra', 'fractions'), 'math', 2000, None, True),
]
prediction_time = 3000
candidates = ('algebra', 'fractions', 'geometry')

# Compute one historical feature dictionary for each candidate concept.
features = {
    concept: extract_features(history, concept, prediction_time)
    for concept in candidates
}
print('Algebra accuracy:', features['algebra']['skill_accuracy'])
print('Algebra mean duration:', features['algebra']['skill_avg_response_time'])
print('Geometry accuracy:', features['geometry']['skill_accuracy'])

# This is the ordered raw input, before any future model preprocessing.
raw_algebra_row = [features['algebra'][name] for name in FEATURE_NAMES]
assert len(raw_algebra_row) == 12

# Placeholder outputs supplied externally; no neural inference occurs here.
error_probabilities = {'algebra': 0.8, 'fractions': 0.3, 'geometry': 0.5}
last_reviewed = {}
for interaction in history:
    if interaction.timestamp_ms < prediction_time:
        for concept in interaction.concept_ids:
            last_reviewed[concept] = interaction.timestamp_ms

selection = select_concept(error_probabilities, last_reviewed, prediction_time)
print('Selected:', selection.concept_id, round(selection.score, 6))

# A future generator would supply this candidate's contents.
question = Question(
    question_id='q3',
    concept_ids=(selection.concept_id,),
    subject_id='math',
    question_text='Solve x + 2 = 5. What is x?',
    answer_options=('2', '3', '5'),
    correct_answer='3',
    explanation='Subtract 2 from both sides to obtain x = 3.',
)
validate_question(question)
print('Question structure accepted')

# The application has observed and graded a learner response.
# Grading and storage are outside these components.
new_interaction = Interaction(
    learner_id='learner-1',
    interaction_id='i3',
    question_id=question.question_id,
    concept_ids=question.concept_ids,
    subject_id=question.subject_id,
    timestamp_ms=8000,
    response_time_ms=5000,
    correct=True,
)
history.append(new_interaction)

# The answer contributes only to later predictions, not its own feature row.
assert extract_features(history, 'algebra', 3000) == features['algebra']
print('Later algebra accuracy:', extract_features(history, 'algebra', 9000)['skill_accuracy'])
```

Expected printed output:

```text
Algebra accuracy: 0.5
Algebra mean duration: 4000.0
Geometry accuracy: None
Selected: algebra 0.64
Question structure accepted
Later algebra accuracy: 0.6666666666666666
```

## Why these values appear

Both prior questions involve algebra, with one correct answer out of two. Only
the first question has a known duration, so the mean is 4000 ms. Geometry has no
history: its accuracy is unknown, not zero. Its recency score is one, giving it
priority `0.8 * 0.5 + 0.2 * 1 = 0.6`. Algebra's review was only one second ago, so
its recency contribution is tiny and its priority rounds to 0.64, which wins.

The new interaction's timestamp represents answer availability. Although its
response duration is 5000 ms, the feature extractor never adds this duration to
the timestamp: the source adapter must define timestamp semantics consistently.
The answer at 8000 ms is excluded from the prediction at 3000 ms and included at
9000 ms, when algebra has two correct answers out of three attempts.

## Integration responsibilities

| Stage | Implemented in P2 | Integrating application supplies |
| --- | --- | --- |
| Source ingestion | Validated internal Interaction record and in-memory repository | Dataset mapping and timestamp conversion |
| Historical statistics | Fixed 12-feature dictionary per target concept | Learner grouping, train/test splits, imputation, scaling, and tensors |
| Prediction | No neural predictor | Shared LSTM and any trained subject heads |
| Practice selection | Injected ConceptSelector and probability/recency scoring | Eligible concepts, real predictor adapter, and shared repository adapter |
| Question generation | Question container and structural checks | FLAN-T5-small invocation, parsing, and factual verification |
| Response handling | Interaction validation | Answer grading, unique IDs, logging, and persistence |

For a structurally rejected generated question, the caller can catch `ValueError`
and decide whether to regenerate. Structural acceptance alone is not permission
to trust its factual claims. No regeneration or factual-verification service is
implemented in this iteration.
