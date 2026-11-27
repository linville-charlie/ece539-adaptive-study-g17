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
"""Source events retain provenance that the app's single-learner schema omits."""

import json
from collections.abc import Iterable, Iterator
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class TrainingEvent:
    """One question, even when it assesses several concepts.

    prediction_timestamp_ms is presentation time. timestamp_ms is estimated answer
    availability. Use only answers available strictly before presentation when
    making a training input; the target correctness belongs exclusively in labels.
    """

    learner_id: str
    interaction_id: str
    question_id: str
    concept_ids: tuple[str, ...]
    timestamp_ms: int
    response_time_ms: int
    correct: bool
    prediction_timestamp_ms: int

    def __post_init__(self) -> None:
        """Reject ambiguous IDs, invalid labels, and impossible event times.

        A dataclass calls this automatically after constructing a TrainingEvent.
        """
        identifiers = (self.learner_id, self.interaction_id, self.question_id)
        for identifier in identifiers:
            if not isinstance(identifier, str) or not identifier.strip():
                message = (
                    "learner, interaction, and question IDs must be nonempty strings"
                )
                raise ValueError(message)

        if not isinstance(self.concept_ids, tuple) or not self.concept_ids:
            message = "concept_ids must be a nonempty tuple"
            raise ValueError(message)
        seen_concept_ids = set()
        for concept_id in self.concept_ids:
            if not isinstance(concept_id, str) or not concept_id.strip():
                message = "concept IDs must be nonempty strings"
                raise ValueError(message)
            if concept_id in seen_concept_ids:
                message = "concept IDs must not repeat within one event"
                raise ValueError(message)
            seen_concept_ids.add(concept_id)

        times = (self.timestamp_ms, self.prediction_timestamp_ms, self.response_time_ms)
        for time_ms in times:
            # bool is a subclass of int, so type(...) rejects True/False as times.
            if type(time_ms) is not int or time_ms < 0:
                message = "event times must be nonnegative integer milliseconds"
                raise ValueError(message)
        if self.timestamp_ms < self.prediction_timestamp_ms + self.response_time_ms:
            message = "answer availability precedes estimated response completion"
            raise ValueError(message)
        if type(self.correct) is not bool:
            message = "correct must be a boolean label"
            raise ValueError(message)


def write_events(path: Path, events: Iterable[TrainingEvent]) -> None:
    """Write one grouped source question per line, preserving multi-tag identity."""
    with path.open("w", encoding="utf-8") as output:
        for event in events:
            event_dictionary = asdict(event)
            json_line = json.dumps(event_dictionary, sort_keys=True)
            output.write(json_line + "\n")


def read_events(path: Path) -> Iterator[TrainingEvent]:
    """Read files produced by the converter; IDs are strings, times milliseconds."""
    with path.open(encoding="utf-8") as source:
        for line_number, line in enumerate(source, 1):
            try:
                yield _decode_event(line)
            except (TypeError, ValueError) as error:
                message = f"{path}:{line_number}: {error}"
                raise ValueError(message) from error


def _decode_event(line: str) -> TrainingEvent:
    """Decode a single JSON object before attaching file and line context."""
    data = json.loads(line)
    if not isinstance(data, dict) or not isinstance(data.get("concept_ids"), list):
        message = "expected an event object with a concept_ids array"
        raise TypeError(message)
    data["concept_ids"] = tuple(data["concept_ids"])
    return TrainingEvent(**data)
