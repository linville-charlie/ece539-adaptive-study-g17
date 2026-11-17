# Integration notes and repository inspection

## Latest repository and PR inspection (November 14, 2026)

Work is on the requested local `p2-branch`, created from `main` at `9975df7`.
The previous uncommitted P2 implementation was retained. All implementation and
documentation remain in P2; no teammate branch was merged or modified. The current
main has only workspace READMEs, with no shared source, model interface, or tests.

Live GitHub inspection covered all listed PRs, their metadata and changed files,
review discussions and inline threads, branch names, main README, and related
issues #1, #3, #5, and #8. Only PRs #6 and #7 were found; both are open/unmerged.
The local remote-tracking SHAs matched their live PR heads, so their commits and
source contents could be inspected without checking out or merging either branch.

| Source | Inspected head | Status / scope |
| --- | --- | --- |
| [PR #6](https://github.com/linville-charlie/ece539-adaptive-study-g17/pull/6) | `de414dcf4380c39a69aafcc73831d0b98c38794b` | Open; 3 commits, README-only feature proposal |
| [PR #7](https://github.com/linville-charlie/ece539-adaptive-study-g17/pull/7) | `fa84682d4f5a92c283efd7848227c2fcccc56a82` | Open; 4 commits, 28 changed files, architecture/configuration stubs |
| `main` | `9975df76411fc9d52b634d7343aadb8d50189e25` | Base of both PRs and p2-branch; neither design is merged |

PR #6 commits are `443f107` (draft), `0c90092` (additional data), and `de414dc`
(input-list tweaks). PR #7 commits are `19260fa` (initial design), `82dc0a7`
(finished design), `a4cc22c` (string fixes), and `fa84682` (controller import order).
No inline review threads were returned. PR #6 has no discussion comments. PR #7's
review timeline confirms the selector/controller handoff, a per-instance local
learner database, and a request to leave functional work for separate tasks.
An additional review says the design looks good; the PR is still unmerged.

### Implemented by teammates versus placeholders

PR #7 defines the shared source layout: `src/database/`, `src/questions/`, and
`src/ece539_adaptive_study_g17/ui/`. It contains ORM declarations, table-name
constants, question types, UI constructors, project configuration, and method
signatures. `DatabaseController`, `ConceptSelector`, `ConceptEvaluationData`,
QuestionController behavior, generator behavior, and the complete UI workflow are
still placeholders. No persistent learner-attempt model or neural inference API
was found. Docstring-only methods do not yet provide working behavior.

Reuse the teammate's controller, Concept/fact records, and selector facade during
integration. P2 supplies their feature/ranking implementation and explicit adapters,
rather than replacing the controller, database, or UI. Since the src design is
unmerged and incomplete, this branch deliberately has no runtime dependency on it.

The design branch declares Python >=3.14, Ruff/pre-commit, SQLAlchemy, torch, and
ollama. P2 leaves project-wide versions/dependencies untouched. It remains usable
independently on Python 3.10+ and is tested here on Python 3.12.3. Integrated Python
3.14 and the design branch's full lint configuration remain deployment checks.

## ORM recheck: corrected and remaining issues

These are static source observations at PR #7 head, not an execution of its ORM.

| Earlier finding | Latest revision |
| --- | --- |
| Concept.field_id used a column-name string | Corrected to ForeignKey(FIELD_TABLE_ID) |
| FieldColumn.field_id targeted a table rather than column | Corrected to ForeignKey(FIELD_TABLE_ID) |
| Misspelled Field.field_coulmns | Corrected to field_columns |
| Fact and FieldColumn shared a table name | Corrected; FACT_TABLE is distinct from FIELD_COLUMN_TABLE |
| Field, FieldColumn, Fact lacked the declarative base | Still present; only Concept inherits _BaseDatabaseTable |
| Collection relationship annotations | Still scalar-shaped: Field.field_columns and FieldColumn.facts need cardinality agreement/list annotations |
| Learner response storage | Still no persistent Attempt model or history retrieval method |
| ConceptEvaluationData contents | Still empty; ID/subject fields and learner context are not agreed |
| DatabaseController.get_concept_by_id | Still lacks an ID parameter in its stub signature |

Also, the concept training-data TODO must not become a single global mastery value.
The per-instance local database can represent one learner, but statistics must
still be derived from that learner's attempts rather than shared concept content.
The adapter accepts a session learner ID, which also supports learner-disjoint
training/evaluation histories without requiring a multi-user hosted application.

None of these teammate definitions were edited. The corrected findings above
supersede the earlier inspection at commit 82dc0a7; they are not current bugs.

## SQLite adapter contract

The shared DatabaseController can implement the proposed
`get_attempt_history(learner_id, before_timestamp_ms=None)` method. Wrap it in
`DatabaseAttemptRepository(controller)` to satisfy P2's
`AttemptRepository.get_history(...)` protocol. This method is a requested shared
addition, not something already implemented by PR #7. Alternatively, implement
get_history directly in a shared repository. Either implementation should:

1. Filter attempt rows by the requested learner.
2. When supplied, apply a strict timestamp cutoff (`timestamp_ms < cutoff`).
3. Load all associated concept IDs for each response without duplicating attempts.
4. Order by answer-availability timestamp and a stable source order for ties.
5. Convert source/ORM IDs to consistently namespaced strings and times to integers
   in milliseconds, preserving missing durations as `None`.
6. Return `Interaction` records with observed boolean correctness.

Persist individual attempts, including submitted answer, question association,
learner association, concept association, timestamp, duration, and correctness.
An interaction ID must identify a response event, not merely a question: a learner
can answer the same question repeatedly. Global event-ID uniqueness should be
maintained by the shared persistence layer. Submitted answer is not currently a
field in P2's Interaction; use it in the shared database for grading/auditing and
map only the declared fields into this package.

Do not persist one global `Concept.accuracy` or mutate concept facts to represent
learner mastery. Derived statistics depend on learner and prediction cutoff.

## Existing selector and controller adaptation

The design branch has `questions.question_selector.ConceptSelector` with
`__init__(database_controller)` and a stub
`select_concept(concept_eval_data) -> Concept`. P2's implementation is the concrete
non-neural service behind that proposed role. It does not replace that module.
`ControllerConceptSelector` now provides that select_concept method shape and
returns the project's own Concept object through explicit callbacks. At integration,
the existing facade can delegate to it. Its additional constructor dependencies
must be supplied by composition; this is not a drop-in replacement for the empty
one-argument constructor. No assumptions are made about the empty evaluation DTO.

```python
from non_neural import (
    CandidateConcept, ConceptSelector, ControllerConceptSelector,
    DatabaseAttemptRepository,
)

# Integration sketch: these names are supplied by the shared application.
core = ConceptSelector(DatabaseAttemptRepository(database_controller), predictor)
facade = ControllerConceptSelector(
    core,
    learner_id=session_learner_id,
    to_candidate=map_project_evaluation_to_candidate,
    get_concept_by_id=lookup_project_concept,
    prediction_clock_ms=clock_ms,
)
chosen_project_concept = facade.select_concept(eligible_evaluation_records)
# The controller retrieves chosen_project_concept.facts and owns generation/Q&A.
# facade.last_selection contains the winning score after a successful lookup.
```

The callbacks are explicit integration dependencies, not implemented ORM methods.
For integer ORM keys, lookup_project_concept must reverse the agreed string-ID
mapping; do not cast arbitrary globally namespaced IDs to integers. The clock must
use the same time origin as attempt timestamps.

| Existing role | P2 connection |
| --- | --- |
| DatabaseController | Supply an AttemptRepository adapter and keep concept/fact retrieval there |
| ConceptEvaluationData | Map agreed concept and subject identity to CandidateConcept; do not store global learner accuracy |
| Existing ConceptSelector facade | Hold a P2 ConceptSelector configured with the repository and model adapters |
| QuestionController.select_next_question | Pass the current learner, eligible concepts, and prediction cutoff to select_next_concept |
| Selected Concept | Retrieve the ORM concept using the returned concept ID, then load context facts |
| Question generation | Parse output into P2 Question fields and call QuestionValidator |
| QuestionController.accept_quesiton_answer | Existing misspelled stub needs coordination; grade/log the response into shared persistence |

The inspected `DatabaseController.get_concept_by_id()` stub has no ID parameter;
its final lookup contract needs agreement. Concept-to-subject mapping is also not
yet defined in the stub ORM. Do not silently assume that a user-defined `Field`
always equals a training subject; agree that mapping explicitly.

The teammate's `questions.question.Question` represents a concept, context facts,
answer fact, and question type. P2's `Question` is a generated multiple-choice
output record. They serve different stages. An adapter should preserve source
fact provenance while supplying the validator's text/options/answer fields.

## Predictor adapter and unresolved sequence input

No neural inference interface is present in either PR. P2 therefore offers two
explicit, alternative injection paths; exactly one must be provided:

- `predictor=` implements the retained ErrorPredictor method with learner ID,
  concept ID, subject ID, and one target-context feature dictionary.
- `sequence_predictor=` implements SequenceErrorPredictor.predict_error(request),
  receiving a PredictionRequest with learner/concept/subject metadata, cutoff,
  chronological strictly prior raw interactions, read-only target-context features,
  and the ordered 12 values plus observation mask.

The request path gives a sequence-based model the information it needs without
forcing it into a flat dictionary or making another unfiltered history query.
Even if the repository returns future rows, neither predictor path receives their
answer fields. Both validate returned error probabilities and share the same
ranking/failure policy. A correctness predictor must convert its output with 1-p.

A request's raw history is not a ready-made LSTM tensor. The neural teammate must
agree how to form historical rows at each historical cutoff, encode concept/subject
identifiers, scale values, handle missing observations, and pad/mask variable-length
sequences. A history row's label must not enter its own historical input row.
Known historical correctness may be used only as allowed by the eventual model's
sequence/label alignment. The final tensor layout remains unresolved.

`to_feature_vector` retains exactly 12 values with a separate observation mask.
A False mask entry distinguishes unknown accuracy from known zero. Do not append
IDs or masks to the agreed vector without a model-interface decision. The mask
is not a sequence-padding mask, and placeholder zeros alone do not preserve
missingness unless the model actually consumes the observation mask.

## Failure and verification policies

Selection fails by default when inference raises; the controller can report the
failure or retry. An explicit fixed fallback probability enables continued ranking
and marks the returned winning result with `used_fallback=True` if it used that
fallback. `rank_concepts` returns every candidate's score breakdown and fallback flag;
`select_next_concept` returns the first result. A controller needing exception
telemetry should wrap the predictor with logging; raw exception details are not
stored in ranking records. Invalid
probabilities and repository failures are not masked by this fallback.

A structurally valid question can still be false. The application must separately
check source support, correctness, relevance, and explanation quality before
presentation. Rejection/regeneration limits and factual-verification methods are
integration decisions. Qwen versus FLAN is still under evaluation; P2 neither
loads those models nor commits the team to one.
