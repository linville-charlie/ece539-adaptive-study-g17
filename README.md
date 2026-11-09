# ece539-adaptive-study-g17

ECE 539 Team G17 integration project: adaptive study question selection and
generation.

## Workspace layout

- `P1/` through `P4/`: individual teammate workspaces.
- `final/`: integrated team deliverable.

The member-to-workspace mapping belongs in the private Canvas proposal.

## Project TODOs

### Design and Preperatory Work (Nov. 1 - Nov. 8)

- [ ] Determine input data format
- [ ] Assemble training, testing, and evaluation datasets
- [ ] Prepare compute for training
- [ ] Identify backup compute
- [ ] Design non-neural components

### Main Development (Nov. 9 - Nov. 22)

- [ ] Develop non-neural components
- [ ] Write unit tests for components
- [ ] Train primary model
- [ ] Train backup model

### Integration and Testing (Nov. 23 - Nov. 29)

- [ ] Smoke testing
- [ ] Write and run integration tests

### Presentation & Final Report Preparation (Nov. 30 - Dec. 6)

- [ ] Prepare and practice presentation
- [ ] Create presentation slide deck
- [ ] Create final report

## Concepts and Question Generation

The User is expected to input various 'concepts' they wish to study into the
project. Each concept is an entry in a user-defined 'field', or a table of
entries with a specific, user-defined schema. Concepts represent linked data;
this could be the declentions of a noun in various numbers/cases/etc. that the
user wishes to practice; or a collection of names, faces, and other associated
informaiton that a teacher or new employee wishes to learn rapidly; or just a
term-definition pair.

An artifical neural network then makes its best guess as to which concept the
user is least likely to have learned (i.e., least likely to get a question on it
right), and provides the information to a process invlolving small language
model to generate a question around.

## ANN Input Data

The following data will be provided to the model.

#### Input Data

- **`previous_response_time`** — Time spent answering the previous question.
- **`previous_correct`** — Whether the previous answer was correct.
- **`time_since_previous_interaction`** — Time elapsed since the student's last
	interaction.
- **`time_since_last_skill_attempt`** — Time since the specific concept was last
	practiced.
- **`skill_attempt_count`** — Number of previous attempts on that concept.
- **`skill_avg_response_time`** — Average response time for that concept.
- **`skill_accuracy`** — Overall historical accuracy for that concept.
- **`recent_skill_avg_response_time`** — Average response time over _recent_
	attempts.
- **`recent_skill_accuracy`** — Accuracy over the most _recent_ attempts.
- **`skill_correct_streak`** — Number of consecutive correct responses for the
	concept.
- **`overall_accuracy`** — Student's accuracy across all previous questions.
- **`overall_attempt_count`** — Total number of previous questions answered.
- **`concept_id`** — A numberic identifier for a concept
- **``**

#### Additional training data

The following data may be used during training, but will otherwise not be given
to the model.

- **`learner_id`** — Allows for training to keep track of multuple learners.
- **`timestamp`** — The timestamp data used to calculate some of the above
	features.
- **`response_time`** — Response time data extracted to calculate some of the
	above features.
- **`correct`** — Accuracy data  extracted to calculate some of the above
	features.

'Recent' is defined to be the `floor(10*log(skill_attempt_count+1))` most recent
instances of the question being asked, or the most recent 50 times. [1]

---
1. This provides for 125,891 asks about a concept before the definition changes;
	or 12,589,254,116 if the last 100 results are stored instead.