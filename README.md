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

- **`time_last_asked`** A timestamp representing the last time this user was
	exposed to this concept.
- **`num_times_aksed`** The number of times a question about this topic was
	answered by the User.
- **`ave_time_elapsed`** The average time elapsed considering all questions
	about this concept.
- **`accuracy`** The average accuracy of the User on all questions about this
	concept.
- **`recent_ave_time_elapsed`** The average time elapsed of all _recent_
	questions about this concept.
- **`recent_accuracy`** The average accuracy of the user on all _recent_
	questions about this concept.

'Recent' is defined to be the `floor(10*log(num_times_asked+1))` most recent instances of the question being asked, or the most recent 50 times. [1]

---
1. This provides for 125,891 asks about a concept before the definition changes;
	or 12,589,254,116 if the last 100 results are stored instead.