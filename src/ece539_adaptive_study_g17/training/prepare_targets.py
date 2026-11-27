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
"""Export historical concept features and separate labels without loading an LSTM.

Source events remain the full chronological record. Each target points to a safe
prefix of its learner's source events rather than duplicating entire sequences.
"""

import argparse
import json
from collections.abc import Iterator, Sequence
from itertools import groupby
from pathlib import Path
from shutil import copyfile
from tempfile import TemporaryDirectory

from ece539_adaptive_study_g17.database.attempt import Attempt
from ece539_adaptive_study_g17.database.concept import Concept
from ece539_adaptive_study_g17.database.field import Field  # noqa: F401 -- ORM registry

from .records import TrainingEvent, read_events
from .storage import FEATURE_NAMES

SPLIT_NAMES = ("train", "validation", "test")


def learner_targets(
    events: Sequence[TrainingEvent],
    concept_map: dict[str, int],
    concept_vocabulary: dict[str, int],
) -> Iterator[dict[str, object]]:
    """Replay available answers before each target; keep unseen concepts too.

    Source events must be sorted by answer availability. Targets are processed in
    presentation order so the available-history pointer only moves forwards.
    Simultaneous completions are unavailable at that exact prediction time.
    Shared Concept objects are transient: the original databases are never changed.
    """
    # Start with one learner, then check every event belongs to that learner.
    if not events:
        message = "learner history must not be empty"
        raise ValueError(message)

    expected_learner_id = events[0].learner_id
    previous_timestamp_ms = events[0].timestamp_ms
    seen_interaction_ids = set()

    for event in events:
        if event.learner_id != expected_learner_id:
            message = "all events must belong to the same learner"
            raise ValueError(message)
        if event.timestamp_ms < previous_timestamp_ms:
            message = "learner events must be sorted by answer availability"
            raise ValueError(message)
        if event.interaction_id in seen_interaction_ids:
            message = "duplicate interaction ID in learner history"
            raise ValueError(message)

        previous_timestamp_ms = event.timestamp_ms
        seen_interaction_ids.add(event.interaction_id)
    concept_states: dict[str, Concept] = {}
    history_end_index = 0
    ordered_targets = sorted(events, key=lambda event: event.prediction_timestamp_ms)

    for target in ordered_targets:
        # Add completed source questions once, regardless of their number of tags.
        while (
            history_end_index < len(events)
            and events[history_end_index].timestamp_ms < target.prediction_timestamp_ms
        ):
            completed_event = events[history_end_index]
            for concept_id in completed_event.concept_ids:
                if concept_id not in concept_states:
                    concept_states[concept_id] = Concept(id=concept_map[concept_id])
                concept_states[concept_id].attempts.append(
                    Attempt(
                        timestamp_ms=completed_event.timestamp_ms,
                        response_time_ms=completed_event.response_time_ms,
                        was_correct=completed_event.correct,
                    )
                )
            history_end_index += 1

        for concept_id in target.concept_ids:
            if concept_id not in concept_states:
                concept_states[concept_id] = Concept(id=concept_map[concept_id])
            summary = concept_states[concept_id].get_evaluation_data()
            features = {}
            for feature_name in FEATURE_NAMES:
                features[feature_name] = getattr(summary, feature_name)
            yield {
                "learner_id": target.learner_id,
                "interaction_id": target.interaction_id,
                "concept_id": concept_id,
                "database_concept_id": concept_map[concept_id],
                "embedding_concept_id": concept_vocabulary.get(concept_id, 0),
                "prediction_timestamp_ms": target.prediction_timestamp_ms,
                "history_end_index": history_end_index,
                "features": features,
                "cold_start": summary.attempt_count == 0,
                "label_error": int(not target.correct),
                "weight": 1 / len(target.concept_ids),
            }


def write_target_split(
    source_path: Path,
    output_path: Path,
    expected_learners: list[str],
    concept_map: dict[str, int],
    concept_vocabulary: dict[str, int],
) -> dict[str, int]:
    """Write one split while holding only one learner's source history in memory."""
    learner_ids: list[str] = []
    counts = {
        "questions": 0,
        "targets": 0,
        "cold_start_targets": 0,
        "incorrect_targets": 0,
        "unknown_concept_targets": 0,
    }
    with output_path.open("w", encoding="utf-8") as output:
        for learner_id, group in groupby(
            read_events(source_path), key=lambda event: event.learner_id
        ):
            learner_ids.append(learner_id)
            events = list(group)
            counts["questions"] += len(events)
            for target in learner_targets(events, concept_map, concept_vocabulary):
                output.write(json.dumps(target, sort_keys=True) + "\n")
                counts["targets"] += 1
                counts["cold_start_targets"] += int(target["cold_start"])
                counts["incorrect_targets"] += int(target["label_error"])
                counts["unknown_concept_targets"] += target["embedding_concept_id"] == 0
    if learner_ids != expected_learners:
        message = f"{source_path}: learner groups do not match the source manifest"
        raise ValueError(message)
    return counts


def read_json_file(file_path: Path) -> dict[str, object]:
    """Read a JSON file into a Python dictionary."""
    with file_path.open(encoding="utf-8") as input_file:
        return json.load(input_file)


def validate_split_learners(source_manifest: dict[str, object]) -> None:
    """Check that each learner appears exactly once across the three splits."""
    seen_learner_ids = set()
    for split_name in SPLIT_NAMES:
        learner_ids = source_manifest["learners"][split_name]
        for learner_id in learner_ids:
            if learner_id in seen_learner_ids:
                message = "source manifest repeats a learner within or across splits"
                raise ValueError(message)
            seen_learner_ids.add(learner_id)


def write_target_metadata(
    dataset_dir: Path,
    working_dir: Path,
    manifest: dict[str, object],
) -> None:
    """Copy the source metadata and save a readable summary of this export."""
    for filename in ("concept_map.json", "vocabularies.json"):
        source_path = dataset_dir.joinpath(filename)
        destination_path = working_dir.joinpath(filename)
        copyfile(source_path, destination_path)

    manifest_path = working_dir.joinpath("manifest.json")
    with manifest_path.open("w", encoding="utf-8") as output_file:
        json.dump(manifest, output_file, indent=2, sort_keys=True)
        output_file.write("\n")


def prepare_targets(dataset_dir: Path, output_dir: Path) -> dict[str, object]:
    """Read a prepared dataset, export targets, and save their metadata.

    dataset_dir is the existing input folder; output_dir is the new result folder.
    Work happens in a temporary folder first. If anything fails, Python removes
    that folder automatically. Only a complete export becomes output_dir.
    No model is loaded and the input files and databases are left unchanged.
    """
    # 1. Refuse to replace an existing export.
    if output_dir.exists():
        raise FileExistsError(output_dir)

    source_manifest_path = dataset_dir.joinpath("manifest.json")
    concept_map_path = dataset_dir.joinpath("concept_map.json")
    vocabularies_path = dataset_dir.joinpath("vocabularies.json")

    # 2. Read the input metadata and make sure learners do not cross splits.
    source_manifest = read_json_file(source_manifest_path)
    concept_map = read_json_file(concept_map_path)
    vocabularies = read_json_file(vocabularies_path)
    concept_vocabulary = vocabularies["concepts"]
    validate_split_learners(source_manifest)

    # Build the export separately so a failed run does not leave partial results.
    output_parent = output_dir.parent
    output_parent.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix="ednet-targets-", dir=output_parent) as temporary:
        working_dir = Path(temporary).joinpath("targets")
        working_dir.mkdir()
        split_counts = {}

        # 4. Export training, validation, and test data separately.
        for split_name in SPLIT_NAMES:
            filename = f"{split_name}.jsonl"
            source_path = dataset_dir.joinpath(filename)
            destination_path = working_dir.joinpath(filename)
            expected_learners = source_manifest["learners"][split_name]

            counts = write_target_split(
                source_path,
                destination_path,
                expected_learners,
                concept_map,
                concept_vocabulary,
            )
            expected_question_count = source_manifest["interaction_counts"][split_name]
            if counts["questions"] != expected_question_count:
                message = f"{split_name}: question count does not match source manifest"
                raise ValueError(message)
            split_counts[split_name] = counts

        # Keep only the metadata needed to use the targets.
        manifest = {
            "format_version": 2,
            "source_dataset": str(dataset_dir.resolve()),
            "feature_names": FEATURE_NAMES,
            "counts": split_counts,
            "label_policy": "1 = incorrect, 0 = correct; excluded from features",
            "history_policy": "availability strictly before target presentation",
            "history_index_policy": "learner source events[:history_end_index]",
            "weight_policy": "1 / source question tag count",
            "trained_model": False,
        }
        write_target_metadata(dataset_dir, working_dir, manifest)

        # Move the finished export out before the temporary folder is removed.
        working_dir.rename(output_dir)
    return manifest


def main() -> None:
    """Export model-independent dataset targets from an existing prepared dataset."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    arguments = parser.parse_args()
    print(
        json.dumps(
            prepare_targets(arguments.dataset_dir, arguments.output_dir), indent=2
        )
    )


if __name__ == "__main__":
    main()
