"""Synthetic feature extraction and ranking; no model, GPU, or SQLite required.

Run from the repository root:
    PYTHONPATH=P2 P2/.venv/bin/python P2/examples/demo_pipeline.py

The probabilities below are fixed test fixtures, not real LSTM predictions.
"""
from non_neural import (
    CandidateConcept, ConceptSelector, InMemoryAttemptRepository, Interaction,
    MockErrorPredictor, extract_features, to_feature_vector,
)


def main() -> None:
    """Print historical features, masks, full candidate ranking, and the winner.

    Uses one synthetic learner with three concepts across two subjects. Algebra
    and fractions were answered recently, while geography is never reviewed.
    Nothing is persisted and no external dependencies are loaded at runtime.
    """
    attempts = [
        Interaction('learner-1', 'i1', 'q1', ['algebra'], 'math', 1000, 4000, False),
        Interaction(
            'learner-1', 'i2', 'q2', ['algebra', 'fractions'], 'math',
            2000, None, True,
        ),
        Interaction('other-learner', 'i3', 'q1', ['algebra'], 'math', 1000, 1000, True),
    ]
    repository = InMemoryAttemptRepository(attempts)
    cutoff = 3000
    features = extract_features(repository.get_history('learner-1', cutoff), 'algebra', cutoff)
    print('SYNTHETIC attempts; MOCK probabilities (no trained models)')
    print('Historical features:', features)
    print('Masked vector:', to_feature_vector(features))
    predictor = MockErrorPredictor({
        ('math', 'algebra'): .8,
        ('math', 'fractions'): .3,
        ('geography', 'capitals'): .5,
    })
    selector = ConceptSelector(repository, predictor)
    ranking = selector.rank_concepts(
        learner_id='learner-1',
        candidate_concepts=[
            CandidateConcept('algebra', 'math'),
            CandidateConcept('fractions', 'math'),
            CandidateConcept('capitals', 'geography'),
        ],
        prediction_timestamp_ms=cutoff,
    )
    print('Ranking (highest priority first):')
    for result in ranking:
        print(
            f'  {result.concept_id}: error={result.predicted_error_probability:.3f}, '
            f'recency={result.recency_score:.9f}, score={result.selection_score:.9f}',
        )
    # Reuse the ranking's winner; calling select_next_concept here would infer again.
    selected = ranking[0]
    print(f'Selected: {selected.concept_id}; score={selected.selection_score:.9f}')


if __name__ == '__main__':
    main()
