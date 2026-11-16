# ece539-adaptive-study-g17
ECE 539 Team G17 integration project: adaptive study question selection and generation

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

## Project Architecture Notes
- Database - hold concepts, IDs, terms, users, timestamp, right/wrong. Scores will then be stored in the database - figure out how to combine score, streak, and when the question was last asked.

- Our model - our model chooses the next concept ID, based on the history of each concept.

- ** Something else chooses the actual question of fact from each concept.

- Qwen - generates a question based on the chosen question; the user then sends their answer back to Qwen, which determines if the question is right or wrong. Tell which type of question we want.

- **Language model will help determine if the user input for the answer to the question is close enough to the given question's correct answer. The language model will say yes or no to if the question was correct.

- **update step - update the score and history data. Timestamp, how many times it's correct, etc. (Total times seen, Total times right, Right in the past “100” times asked, Time last seen, Time spent on the question??)

