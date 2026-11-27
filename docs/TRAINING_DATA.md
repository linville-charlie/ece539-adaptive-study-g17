<!-- Author: Aniketh Kancherla -->
# Preparing the EdNet dataset

The dataset code converts EdNet practice histories into our shared database format
and exports training targets. It does not train the LSTM or change the app's
concept-and-facts structure.

## Files

| File | Purpose |
| --- | --- |
| `training/records.py` | Define a question attempt and read/write JSONL records. |
| `training/extract_ednet.py` | Select learner CSVs from the downloaded ZIP. |
| `training/storage.py` | Save one learner's concepts and attempts to SQLite. |
| `training/prepare_ednet.py` | Convert CSVs, split learners, and save ID maps. |
| `training/prepare_targets.py` | Build historical features and separate labels. |

The Python files are under `src/ece539_adaptive_study_g17/`.
Each includes Aniketh Kancherla's author tag.

## Run the preparation

Download KT1 and Contents from the [official EdNet repository](https://github.com/riiid/ednet).
Keep the ZIP at `data/raw/KT1.zip` and the question metadata at
`data/raw/contents/questions.csv`. Follow EdNet's usage and attribution terms.
The `data/` folder is ignored by Git.

Run these commands from the project root, using a new output folder each time:

```sh
PYTHONPATH=src .venv/bin/python -m ece539_adaptive_study_g17.training.extract_ednet \
  --archive data/raw/KT1.zip --output-dir data/raw/KT1-1000 --count 1000 --seed 539

PYTHONPATH=src .venv/bin/python -m ece539_adaptive_study_g17.training.prepare_ednet \
  --kt1-dir data/raw/KT1-1000 \
  --questions-csv data/raw/contents/questions.csv \
  --output-dir data/prepared/ednet-1000 --seed 539

PYTHONPATH=src .venv/bin/python -m ece539_adaptive_study_g17.training.prepare_targets \
  --dataset-dir data/prepared/ednet-1000 \
  --output-dir data/prepared/ednet-1000-targets
```

For a small example, convert `examples/ednet_sample/KT1` with its adjacent
`questions.csv`. Those files are invented examples, not actual EdNet records.

## Saved data

The converted dataset contains:

- One SQLite database per learner under `databases/train`, `validation`, or `test`.
- `train.jsonl`, `validation.jsonl`, and `test.jsonl`, with one source question per line.
- `concept_map.json`, mapping skill tags to database IDs.
- `vocabularies.json`, mapping training concepts to embedding IDs. Zero means unknown.
- `manifest.json`, recording learner membership, counts, exclusions, seed, and timing rules.

Learners are split approximately 70/15/15. A learner cannot appear in two splits.
The database IDs and embedding IDs are separate mappings; do not interchange them.
Only training learners determine the embedding vocabulary.

EdNet skill tags stand in for concepts. The shared Fact and FieldColumn tables
stay empty because EdNet metadata does not supply the study facts or question text.
Users still supply those for the actual application. EdNet's multiple-choice
correctness labels do not establish performance on Qwen-graded short answers.

One multi-tag question stays one JSONL event but creates one Attempt row per tag.
Blank answers and questions without usable tags are excluded and counted, rather
than assigned invented labels or concepts. Invalid columns, values, and timestamps
produce errors. A learner with no usable questions cannot be converted.

## Training targets

The target folder contains three JSONL files, the two ID maps, and a short manifest.
Each target row has:

- `features`: the six values from the merged `Concept.get_evaluation_data()` method.
- `label_error`: 1 for incorrect, 0 for correct, separate from the features.
- `cold_start`: whether this concept has no available previous attempts.
- `weight`: one divided by the question's tag count, so question weights total one.
- Source, database, and embedding concept IDs, plus learner/interaction IDs.
- The prediction time and `history_end_index` for finding earlier source events.

The features are attempt count, average response time, accuracy, recent average
response time, recent accuracy, and correct streak. The shared extractor uses
`min(n, 50, floor(10 * log10(n + 1)))` recent attempts and integer average times.
Zero-history targets stay in the dataset with the shared zero placeholders.

Only answers available **strictly before** a question's presentation can contribute
to its features. A completion at the exact presentation time is excluded. KT1 does
not provide definitive submission times, so we estimate availability using the
latest `timestamp + elapsed_time` within each solving_id bundle. Excluded rows also
contribute to bundle timing. Equal-time answers retain source CSV order.

To resolve history, load the original learner's source JSONL events in their stored
availability order, then take `events[:history_end_index]`. Keep that source dataset
with the targets. Do not use a learner's final database summary for every past
question: it would include future answers.

The existing LSTM adapter still expects twelve features. This export follows the
merged six-feature database contract; it is not a replacement tensor adapter.
The current `make_samples()` also uses completion time as its prediction cutoff.
Connecting these targets requires respecting their presentation-time cutoffs.
No model code or architecture was changed here.

## Local dataset

The seed-539 sample contains 1,000 of the archive's 784,309 learners:

| Split | Learners | Questions | Per-concept targets |
| --- | ---: | ---: | ---: |
| Training | 700 | 97,998 | 235,092 |
| Validation | 150 | 27,947 | 65,521 |
| Test | 150 | 12,729 | 28,024 |

There were 84 exclusions: 26 untagged questions and 58 blank answers.
The full archive has not been converted and no model has been trained here.
The older local exports may contain file hashes and extra metadata. New exports
omit those details; question records, features, labels, and database rows are unchanged.

`joinpath("manifest.json")` means the named file inside a folder. A
`TemporaryDirectory` is a disposable working folder: on failure it is removed;
on success the completed output is moved out first. This prevents incomplete
results from being mistaken for a finished dataset.
