# Non-neural API reference

Import the public API with `from non_neural import ...` when running Python from
`P2/`. From the repository root, set `PYTHONPATH=P2`. See the [README](../README.md)
for environment setup and the full feature definitions, and the
[walkthrough](WALKTHROUGH.md) for a complete example.

## Interaction

```python
Interaction(
    learner_id: str,
    interaction_id: str,
    question_id: str,
    concept_ids: tuple[str, ...] | list[str],
    subject_id: str,
    timestamp_ms: int,
    response_time_ms: int | None,
    correct: bool,
)
```

An immutable record validated during construction. All fields are required,
including `response_time_ms`; pass `None` when it is unknown. IDs must be nonblank
strings and concept IDs must form a nonempty list or tuple without duplicates.
Lists are copied into tuples for immutable storage. Timestamps
and known durations must be nonnegative integers; boolean values are rejected.
Correctness must be a Python `bool`. Invalid field values raise `ValueError`.
Omitting required constructor arguments raises Python's usual `TypeError`.

Except for copying concept lists to tuples, the constructor does not coerce
values, check global uniqueness, or normalize
identifier spelling. Convert dataset values before construction. For example,
convert a source's integer correctness flag to a boolean using an explicit source
mapping; `bool('0')` would incorrectly produce `True`.

## extract_features

```python
extract_features(
    history: Sequence[Interaction],
    target_concept_id: str,
    prediction_timestamp_ms: int,
) -> dict[str, float | int | None]
```

| Argument | Contract |
| --- | --- |
| history | A list or other sequence for one learner with unique interaction IDs; stably sorted internally |
| target_concept_id | Nonblank string, using the same namespace as history concept IDs |
| prediction_timestamp_ms | Nonnegative integer, using the history's timestamp origin |

Returns the 12 keys in `FEATURE_NAMES` order. The dictionary contains counts,
0/1 previous correctness, fractional accuracies, millisecond durations, and `None`
for unknown statistics. Obtain an ordered raw row with:

```python
raw_row = [features[name] for name in FEATURE_NAMES]
```

This row can contain `None`; it is not yet a neural tensor. The model adapter must
apply the team's eventual missing-value and scaling policy.

All records are checked for valid history structure, including records at or after
the cutoff. Statistics then use only timestamps strictly below the cutoff. Mixed
learners, duplicate interaction IDs, non-Interaction elements,
and invalid target IDs or cutoffs raise `ValueError`. A generator is not the
supported input contract; materialize it as a list first.

The implementation validates and stably sorts history, then retains filtered
lists. Runtime includes O(n log n) sorting in the worst case plus concept-membership
checks; temporary storage is linear in history length. Repeated extraction for many concepts currently repeats this work.
Incremental caching is a possible future optimization, not implemented behavior.

## select_concept

```python
select_concept(
    predicted_error_probabilities: Mapping[str, float],
    last_reviewed_ms: Mapping[str, int | None],
    prediction_timestamp_ms: int,
    *,
    alpha: float = 0.8,
    half_life_ms: float = 604800000,
) -> Selection
```

The probability mapping defines the candidate set. Supply **error** probabilities;
if a predictor produces correctness probabilities, convert them with `1 - p`
before calling. Every probability must be a finite real number in [0, 1].

The review mapping contains the latest available review timestamp per concept.
A missing key or `None` means never reviewed. Extra keys are ignored. Review
values for candidates must be nonnegative integer milliseconds no later than the
prediction time. The caller must derive this mapping for the same learner and
prediction cutoff used for features.

`alpha` controls the balance: 1 uses only error probability; 0 uses only recency.
The positive, finite half-life is in milliseconds. A never-reviewed concept has
recency 1, but does not automatically win when alpha is greater than zero.

Returns the frozen dataclass `Selection` with fields `concept_id: str` and
`score: float`. The score is a priority measure, not a calibrated error probability.
Exact ties choose the lexically smallest string ID (`'10'` precedes `'2'`). Invalid
configuration, empty candidates, invalid IDs/probabilities, and future reviews
raise `ValueError`. Runtime and temporary storage are linear in candidate count.

## Question and validate_question

```python
Question(
    question_id: str,
    concept_ids: tuple[str, ...] | list[str],
    subject_id: str,
    question_text: str,
    answer_options: tuple[str, ...] | list[str],
    correct_answer: str,
    explanation: str | None = None,
)

validate_question(question: Question, *, min_options: int = 2) -> None
```

`Question` is an immutable candidate container. Unlike `Interaction`, it does not
validate at construction. Always call `validate_question` before accepting a
candidate. The validator expects a `Question`, not a dictionary or raw model text.
Parse generator output into the declared fields first.

`correct_answer` contains the option text, not an index or letter label unless the
option itself is that label. Options must be a list or tuple with at least the configured number of nonblank
strings (minimum two). Lists are copied into tuples in the candidate record. Matching collapses whitespace and ignores case; duplicates under those
same rules are rejected. For example, `'New  York'` matches `' new york '`, while
`'4.'` does not match `'4'`. IDs use the Interaction identifier rules. An explanation
may be omitted, `None`, or a string, including an empty string.

Success returns `None`; invalid structure raises `ValueError`. The function reports
the first failure rather than collecting every error. It does not modify the
question or decide whether the designated answer is factually correct.

## Error handling

Catch validation failures at the application boundary and decide whether to reject
source data or request another generated candidate:

```python
try:
    validate_question(candidate)
except ValueError as error:
    print(f'Question rejected: {error}')
```

The modules provide no retries, persistence, logging service, or frontend. Such
behavior belongs to the integrating application. Error messages are intended to
help humans diagnose input; avoid treating their exact wording as stable codes.


## FeatureVector and to_feature_vector

```python
to_feature_vector(features: Mapping[str, float | int | None]) -> FeatureVector
```

`features` must contain exactly FEATURE_NAMES; dictionary order is ignored.
The frozen result contains `values: tuple[float, ...]` and
`observed_mask: tuple[bool, ...]`, both of length 12 in FEATURE_NAMES order.
None becomes `0.0` plus False. Known zero becomes `0.0` plus True. Nonfinite,
boolean, and nonnumeric supplied values raise ValueError. This is raw conversion,
not scaling, imputation, sequence packing, or a new feature schema.

## AttemptRepository and adapters

```python
repository.get_history(
    learner_id: str, before_timestamp_ms: int | None = None,
) -> list[Interaction]
```

The protocol returns one learner's chronological history, strictly before the
optional cutoff. See [SQLite integration](INTEGRATION.md) for implementation
responsibilities. `InMemoryAttemptRepository(attempts=())` copies supplied records,
rejects duplicate event IDs, and supports `add(attempt)`. Returned lists are copies.

```python
predictor.predict_error(
    learner_id: str, concept_id: str, subject_id: str,
    features: dict[str, float | int | None],
) -> float
```

The predictor returns error probability. The interface is provisional for future
sequence-aware LSTM integration. `MockErrorPredictor(probabilities)` copies a
mapping keyed by `(subject_id, concept_id)`. Missing keys raise KeyError. It ignores
features and learner ID and is not a trained model.

## ConceptSelector

```python
ConceptSelector(
    repository: AttemptRepository,
    predictor: ErrorPredictor | None = None,
    *, sequence_predictor: SequenceErrorPredictor | None = None,
    alpha: float = 0.8,
    half_life_ms: float = 604800000,
    fallback_error_probability: float | None = None,
)

selector.select_next_concept(
    learner_id: str,
    candidate_concepts: Sequence[CandidateConcept],
    prediction_timestamp_ms: int,
) -> ConceptSelection
```

`CandidateConcept(concept_id, subject_id)` contains nonblank string IDs. Repeated
concept IDs are rejected, even across subjects; globally namespace IDs first.
Exactly one predictor option is required. History is retrieved once. The selector
computes features and calls the predictor
in lexical concept-ID order, making call order and exact-score ties deterministic.
It uses the same exponential recency formula as the standalone select_concept.
Never-reviewed candidates have recency 1 and unknown historical statistics.

The frozen result fields are `concept_id`, `subject_id`,
`predicted_error_probability`, `recency_score`, `selection_score`, and
`used_fallback`. select_next_concept returns the winner.
rank_concepts uses the same arguments and returns a list of all ConceptSelection
records sorted by descending selection_score, then lexical concept_id. Each call
performs inference again; reuse the ranking's first record to avoid duplicate work.

Empty candidates and invalid configuration/returned probabilities raise ValueError.
Inference exceptions become chained PredictionError by default. An explicit
fallback_error_probability supplies a fixed replacement only after inference
exceptions, marking a winning fallback result. It does not suppress invalid
returned probabilities or repository errors. The fixed value is not an estimate
learned from data. A mixed-learner repository response is rejected.

## QuestionValidator and ValidationResult

```python
validator = QuestionValidator(min_options=2)
result = validator.validate(question)  # Question or mapping
```

Returns `ValidationResult(is_valid: bool, errors: tuple[str, ...],
question: Question | None)`. Successful results contain the accepted record and
empty errors. Rejections contain the first error and no accepted question.
Malformed mappings, missing required fields, and unexpected fields return errors.
Invalid min_options configuration raises at construction; it must be an integer
of at least two. Matching rules are the same as the legacy raising helper above.

Mappings accept JSON-style concept and option lists. No model-specific parsing,
factual verification, retry, or persistence is provided. Caller code should gate
presentation on `result.is_valid` and a separate factual-verification policy.


## SequenceErrorPredictor and PredictionRequest

```python
class MySequenceAdapter:
    def predict_error(self, request: PredictionRequest) -> float:
        # Build the team's agreed tensors from request.history and target context.
        # Actual model inference belongs to the neural implementation.
        ...

selector = ConceptSelector(repository, sequence_predictor=my_sequence_adapter)
```

This is a protocol sketch, not a runnable model. Exactly one of predictor or
sequence_predictor must be passed. The sequence path does not force a model to
consume a flat dictionary. PredictionRequest contains:

| Field | Meaning |
| --- | --- |
| learner_id, concept_id, subject_id | Grouping/target/routing metadata |
| prediction_timestamp_ms | Exclusive answer-availability cutoff in milliseconds |
| history | Tuple of chronological prior Interaction records for that learner |
| features | Read-only mapping of 12 target-context historical features |
| feature_vector | FeatureVector containing ordered values and observation mask |

The selector removes all records at/after the cutoff before constructing a request.
Duplicate IDs, malformed records, and another learner's records are rejected.
History preserves repository source ordering for equal prior timestamps. The
request has no target response fields. The legacy path receives a private copy
of the feature dictionary, so predictor mutation cannot alter recency scoring.

Raw history still needs sequence feature construction and proper label alignment.
The request does not define tensor shape, sequence-padding masks, identifier
embeddings, scaling, or training behavior. These are unresolved integration tasks.
Both predictor paths share error-probability validation and exception/fallback
policies. The 12-feature schema remains unchanged.

## DatabaseAttemptRepository

```python
repository = DatabaseAttemptRepository(shared_database_controller)
```

The injected source must implement the proposed
get_attempt_history(learner_id, before_timestamp_ms=None) method and return
Interaction records using the AttemptRepository contract. This adapter only
translates the method name to get_history and validates query values. It creates
no connection, tables, or migrations, and propagates source errors. PR #7 does
not yet provide the source method or attempt model; see the integration guide.

## ControllerConceptSelector

```python
ControllerConceptSelector(
    selector: ConceptSelector,
    *, learner_id: str,
    to_candidate: Callable[[EvaluationT], CandidateConcept],
    get_concept_by_id: Callable[[str], ConceptT],
    prediction_clock_ms: Callable[[], int],
)

facade.select_concept(concept_eval_data: Sequence[EvaluationT]) -> ConceptT
```

This generic adapter preserves PR #7's select_concept method shape and delegates
to the single core ranking implementation. Callbacks explicitly map the unfinished
project evaluation DTO and resolve the selected ID to the project's Concept.
The additional constructor dependencies need explicit composition; this is not
an automatic replacement for the PR's one-argument constructor stub.

The clock runs once per call and must match the history's millisecond time origin.
last_selection contains scoring details after successful selection and lookup;
it starts as None and is cleared before every invocation, including failed ones.
Callback, repository, validation, and prediction errors propagate to the caller.
No ORM models or unmerged modules are imported. See [integration notes](INTEGRATION.md)
for the existing facade's expected wiring and unresolved shared interfaces.

## review_recency

```python
review_recency(last_reviewed_ms, prediction_timestamp_ms, *, half_life_ms=604800000)
```

Returns a float in [0, 1]: None review gives one, zero elapsed gives zero, and one
half-life gives 0.5. All times use milliseconds; the half-life must be positive
and finite. Invalid timestamps, future reviews, or invalid half-lives raise
ValueError. This shared helper keeps functional and orchestrated scoring aligned.
