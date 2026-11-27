#   539g17 Adaptive Study Integration Project
#   Copyright (C) 2026  A. Kancherla, C. Linville, Q. Schultz, E. Wulf.
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as published
#   by the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# Authors of this file:
#
# - Aniketh Kancherla
#
# This file header was last modified 27 Nov 2026.
"""Prepare locally downloaded EdNet KT1 for issue #2, without neural dependencies.

Usage: python -m ece539_adaptive_study_g17.training.prepare_ednet --help
This command never downloads the dataset and refuses to overwrite an output folder.
"""

import argparse
import csv
import json
from collections.abc import Sequence
from dataclasses import asdict
from pathlib import Path
from random import Random
from tempfile import TemporaryDirectory

from .records import TrainingEvent
from .storage import FEATURE_NAMES, write_database

MIN_LEARNERS = 3

SOURCE_URL = "https://github.com/riiid/ednet"


def load_questions(path: Path) -> dict[str, tuple[str, tuple[str, ...]]]:
    """Read question_id/correct_answer/tags metadata into a validated lookup.

    Tags are semicolon-separated source IDs and become namespaced concept strings.
    Unknown (-1/empty) tags are retained as an empty mapping. Malformed tags,
    invalid answer keys, duplicate IDs, or missing columns raise
    ValueError with source location. Other content metadata is not a model feature.
    """
    questions = {}
    with path.open(encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        required_columns = ("question_id", "correct_answer", "tags")
        actual_columns = reader.fieldnames or []
        for column_name in required_columns:
            if column_name not in actual_columns:
                message = "questions.csv requires question_id, correct_answer, tags"
                raise ValueError(message)
        for line_number, row in enumerate(reader, 2):
            try:
                question_id, answer, concepts = _metadata_row(row, questions)
                questions[question_id] = (answer, concepts)
            except (AttributeError, TypeError, ValueError) as error:
                message = f"{path}:{line_number}: {error}"
                raise ValueError(message) from error
    if not questions:
        message = "question metadata is empty"
        raise ValueError(message)
    return questions


def _metadata_row(
    row: dict[str, str],
    questions: dict[str, tuple[str, tuple[str, ...]]],
) -> tuple[str, str, tuple[str, ...]]:
    """Parse/validate one metadata row before the caller adds source location."""
    question_id = row["question_id"].strip()
    answer = row["correct_answer"].strip().casefold()
    tags = row["tags"].split(";")
    if not question_id or answer not in {"a", "b", "c", "d"}:
        message = "invalid question ID or answer key"
        raise ValueError(message)
    if question_id in questions:
        message = "duplicate question_id"
        raise ValueError(message)

    # A question can have several tags. Keep each real tag once, in source order.
    concept_ids = []
    for raw_tag in tags:
        tag = raw_tag.strip()
        if tag in {"", "-1"}:
            continue
        if not tag.isdigit():
            message = "invalid skill tag; do not invent a concept"
            raise ValueError(message)
        concept_id = f"ednet:tag:{tag}"
        if concept_id not in concept_ids:
            concept_ids.append(concept_id)
    concepts = tuple(concept_ids)
    return question_id, answer, concepts


def read_learner(
    path: Path,
    questions: dict[str, tuple[str, tuple[str, ...]]],
) -> list[TrainingEvent]:
    """Convert one KT1 learner CSV, preserving distinct events and multiple tags.

    timestamp is question presentation; timestamp+elapsed_time estimates completion.
    Where solving_id exists, all answers in that bundle become available
    together at its maximum estimated completion. This is a conservative KT1 proxy,
    not an observed KT2 submit event. Prediction cutoffs keep presentation time.
    Unknown question IDs/answers and invalid/negative/missing times raise ValueError.
    A missing response_time_ms cannot be turned into zero to guess answer availability.
    """
    parsed_attempts = []
    completion_by_session: dict[str, int] = {}
    with path.open(encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        required_columns = ("timestamp", "question_id", "user_answer", "elapsed_time")
        actual_columns = reader.fieldnames or []
        for column_name in required_columns:
            if column_name not in actual_columns:
                message = f"{path}: missing required KT1 column {column_name}"
                raise ValueError(message)
        for line_number, row in enumerate(reader, 2):
            try:
                (
                    presentation_timestamp_ms,
                    response_time_ms,
                    question_id,
                    correct,
                    concepts,
                ) = _attempt_row(row, questions)
                solving_session_id = (row.get("solving_id") or "").strip()
                if not solving_session_id:
                    solving_session_id = f"row-{line_number}"
                completion_timestamp_ms = presentation_timestamp_ms + response_time_ms
                completion_by_session[solving_session_id] = max(
                    completion_by_session.get(
                        solving_session_id, completion_timestamp_ms
                    ),
                    completion_timestamp_ms,
                )
                parsed_attempts.append(
                    (
                        line_number,
                        presentation_timestamp_ms,
                        response_time_ms,
                        question_id,
                        correct,
                        concepts,
                        solving_session_id,
                    )
                )
            except (KeyError, AttributeError, TypeError, ValueError) as error:
                message = f"{path}:{line_number}: {error}"
                raise ValueError(message) from error
    learner_id = f"ednet:{path.stem}"
    # Build one source event per labeled question after bundle times are known.
    events = []
    for parsed_attempt in parsed_attempts:
        (
            line_number,
            presentation_timestamp_ms,
            response_time_ms,
            question_id,
            correct,
            concepts,
            solving_session_id,
        ) = parsed_attempt
        if not concepts or correct is None:
            continue
        event = TrainingEvent(
            learner_id=learner_id,
            interaction_id=f"{learner_id}:row:{line_number}",
            question_id=f"ednet:{question_id}",
            concept_ids=concepts,
            timestamp_ms=completion_by_session[solving_session_id],
            response_time_ms=response_time_ms,
            correct=correct,
            prediction_timestamp_ms=presentation_timestamp_ms,
        )
        events.append(event)
    return sorted(events, key=lambda event: event.timestamp_ms)


def _attempt_row(
    row: dict[str, str],
    questions: dict[str, tuple[str, tuple[str, ...]]],
) -> tuple[int, int, str, bool | None, tuple[str, ...]]:
    """Parse a KT1 row; caller attaches source path and line to errors."""
    presentation_timestamp_ms = int(row["timestamp"])
    response_time_ms = int(row["elapsed_time"])
    if presentation_timestamp_ms < 0 or response_time_ms < 0:
        message = "timestamps/durations must be nonnegative milliseconds"
        raise ValueError(message)
    question_id = row["question_id"].strip()
    submitted_answer = row["user_answer"].strip().casefold()
    if submitted_answer not in {"", "a", "b", "c", "d"}:
        message = "invalid submitted answer"
        raise ValueError(message)
    correct_answer, concepts = questions[question_id]
    correct = None
    if submitted_answer:
        correct = submitted_answer == correct_answer
    return presentation_timestamp_ms, response_time_ms, question_id, correct, concepts


def exclusion_counts(
    path: Path,
    questions: dict[str, tuple[str, tuple[str, ...]]],
) -> dict[str, int]:
    """Audit missing labels/tags; total counts their union, not double counting."""
    counts = {"untagged": 0, "unanswered": 0, "total": 0}
    with path.open(encoding="utf-8-sig", newline="") as source:
        for row in csv.DictReader(source):
            untagged = not questions[row["question_id"].strip()][1]
            unanswered = not row["user_answer"].strip()
            if untagged:
                counts["untagged"] += 1
            if unanswered:
                counts["unanswered"] += 1
            if untagged or unanswered:
                counts["total"] += 1
    return counts


def split_files(files: Sequence[Path], seed: int) -> dict[str, list[Path]]:
    """Split whole learners approximately 70/15/15 with all three sets nonempty.

    Filenames identify learners; duplicate stems are rejected. At least three
    files are required. Stable sorting before seeded shuffle makes assignments
    reproducible regardless of filesystem iteration order. No question-level split.
    """
    if len(files) < MIN_LEARNERS:
        message = "at least three learner files are required for disjoint splits"
        raise ValueError(message)
    seen_learner_ids = set()
    for learner_file in files:
        learner_id = learner_file.stem
        if learner_id in seen_learner_ids:
            message = "duplicate learner filenames"
            raise ValueError(message)
        seen_learner_ids.add(learner_id)
    shuffled = sorted(files)
    Random(seed).shuffle(shuffled)
    # Reserve at least one learner for every split, even with only three files.
    train_count = round(0.7 * len(files))
    if train_count < 1:  # noqa: PLR1730 -- Explicit bounds for readability.
        train_count = 1
    largest_train_count = len(files) - 2
    if train_count > largest_train_count:  # noqa: PLR1730 -- Explicit bounds for readability.
        train_count = largest_train_count

    validation_count = round(0.15 * len(files))
    if validation_count < 1:  # noqa: PLR1730 -- Explicit bounds for readability.
        validation_count = 1
    largest_validation_count = len(files) - train_count - 1
    if validation_count > largest_validation_count:  # noqa: PLR1730 -- Explicit bounds for readability.
        validation_count = largest_validation_count

    validation_end = train_count + validation_count
    return {
        "train": sorted(shuffled[:train_count]),
        "validation": sorted(shuffled[train_count:validation_end]),
        "test": sorted(shuffled[validation_end:]),
    }


def prepare_split(
    learner_paths: list[Path],
    questions: dict[str, tuple[str, tuple[str, ...]]],
    concept_map: dict[str, int],
    database_dir: Path,
    jsonl_path: Path,
) -> dict[str, object]:
    """Convert each learner and write its database and grouped question records."""
    database_dir.mkdir()
    summary = {
        "question_count": 0,
        "attempt_count": 0,
        "learners": [],
        "excluded_counts": {},
        "concept_ids": set(),
    }
    with jsonl_path.open("w", encoding="utf-8") as output_file:
        for learner_path in learner_paths:
            events = read_learner(learner_path, questions)
            if not events:
                message = f"{learner_path}: no labeled, tagged questions available"
                raise ValueError(message)

            database_path = database_dir.joinpath(f"{learner_path.stem}.sqlite")
            attempt_count = write_database(database_path, events, concept_map)
            summary["attempt_count"] += attempt_count
            summary["question_count"] += len(events)
            summary["learners"].append(f"ednet:{learner_path.stem}")
            summary["excluded_counts"][learner_path.name] = exclusion_counts(
                learner_path,
                questions,
            )
            for event in events:
                event_dictionary = asdict(event)
                json_line = json.dumps(event_dictionary, sort_keys=True)
                output_file.write(json_line + "\n")
                for concept_id in event.concept_ids:
                    summary["concept_ids"].add(concept_id)
    return summary


def write_dataset_json(working_dir: Path, filename: str, contents: object) -> None:
    """Save a metadata dictionary as indented JSON with a final newline."""
    destination_path = working_dir.joinpath(filename)
    with destination_path.open("w", encoding="utf-8") as output_file:
        json.dump(contents, output_file, indent=2, sort_keys=True)
        output_file.write("\n")


def build_concept_map(
    questions: dict[str, tuple[str, tuple[str, ...]]],
) -> dict[str, int]:
    """Assign database IDs to unique tags in a repeatable sorted order."""
    all_concept_ids = set()
    for _correct_answer, concept_ids in questions.values():
        for concept_id in concept_ids:
            all_concept_ids.add(concept_id)

    concept_map = {}
    for database_id, concept_id in enumerate(sorted(all_concept_ids), start=1):
        concept_map[concept_id] = database_id
    return concept_map


def prepare_dataset(
    kt1_dir: Path,
    questions_csv: Path,
    output_dir: Path,
    *,
    seed: int = 0,
    max_learners: int | None = None,
) -> dict[str, object]:
    """Convert KT1 into shared SQLite databases, JSONL splits, and ID maps.

    output_dir must not exist; a failed conversion leaves no partial destination.
    Memory holds question metadata and one learner's rows, not all interactions.
    max_learners is a seeded random smoke-test subset, not necessarily a
    representative research sample. At least three nonempty learners are required.
    Train-only vocabularies reserve zero for unseen IDs to match Charlie's draft.
    No model is loaded, trained, evaluated, or downloaded.
    """
    if output_dir.exists():
        message = f"refusing to overwrite {output_dir}"
        raise FileExistsError(message)
    if max_learners is not None and (
        type(max_learners) is not int or max_learners < MIN_LEARNERS
    ):
        message = "max_learners must be an integer of at least three"
        raise ValueError(message)
    files = sorted(kt1_dir.glob("*.csv"))
    if max_learners is not None:
        Random(seed).shuffle(files)
        files = files[:max_learners]
    assignments = split_files(files, seed)
    questions = load_questions(questions_csv)
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    # 1. Give every source tag a stable database ID, in sorted order.
    concept_map = build_concept_map(questions)

    # 2. Build in a disposable folder. Only a complete result is moved to output.
    with TemporaryDirectory(
        prefix="ednet-prepare-", dir=output_dir.parent
    ) as temporary:
        working_dir = Path(temporary).joinpath("prepared")
        working_dir.mkdir()
        database_root = working_dir.joinpath("databases")
        database_root.mkdir()
        counts = {}
        learners = {}
        attempt_counts = {}
        excluded_counts = {}
        training_concept_ids = set()

        # 3. Process one split at a time, and one learner at a time within it.
        for split_name, learner_paths in assignments.items():
            database_dir = database_root.joinpath(split_name)
            jsonl_path = working_dir.joinpath(f"{split_name}.jsonl")
            summary = prepare_split(
                learner_paths,
                questions,
                concept_map,
                database_dir,
                jsonl_path,
            )
            counts[split_name] = summary["question_count"]
            attempt_counts[split_name] = summary["attempt_count"]
            learners[split_name] = summary["learners"]
            excluded_counts.update(summary["excluded_counts"])
            if split_name == "train":
                training_concept_ids = summary["concept_ids"]

        # 4. Embedding IDs use training learners only. Zero remains the unknown ID.
        concept_vocabulary = {}
        for embedding_id, concept_id in enumerate(
            sorted(training_concept_ids), start=1
        ):
            concept_vocabulary[concept_id] = embedding_id
        vocabularies = {
            "concepts": concept_vocabulary,
            "subjects": {"english": 1},
            "unknown_id": 0,
        }

        # Save split membership and counts alongside the converted data.
        source_manifest_path = kt1_dir.joinpath("source_manifest.json")
        source_extraction = None
        if source_manifest_path.exists():
            with source_manifest_path.open(encoding="utf-8") as source_file:
                source_extraction = json.load(source_file)
        manifest = {
            "source_extraction": source_extraction,
            "format_version": 3,
            "source": SOURCE_URL,
            "seed": seed,
            "feature_names": FEATURE_NAMES,
            "learners": learners,
            "interaction_counts": counts,
            "stored_attempt_counts": attempt_counts,
            "excluded_questions": excluded_counts,
            "max_learners": max_learners,
            "timestamp_policy": "bundle completion; predict at presentation time",
            "window_policy": "min(n, 50, floor(10*log10(n+1)))",
            "trained_model": False,
        }
        write_dataset_json(working_dir, "vocabularies.json", vocabularies)
        write_dataset_json(working_dir, "concept_map.json", concept_map)
        write_dataset_json(working_dir, "manifest.json", manifest)

        # 6. Keep the finished dataset; the empty temporary folder is cleaned up.
        working_dir.rename(output_dir)
    return manifest


def main() -> None:
    """Run the offline CLI; validation/I/O failures produce a nonzero exit status."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kt1-dir", type=Path, required=True)
    parser.add_argument("--questions-csv", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--max-learners", type=int)
    arguments = parser.parse_args()
    report = prepare_dataset(
        arguments.kt1_dir,
        arguments.questions_csv,
        arguments.output_dir,
        seed=arguments.seed,
        max_learners=arguments.max_learners,
    )
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
