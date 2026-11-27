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
# - Ella Wulf
#
# This file header was last modified 25 Nov 2026.
"""Check the history summary a concept gives the selector."""

from collections.abc import Iterator

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from ece539_adaptive_study_g17.database.attempt import Attempt
from ece539_adaptive_study_g17.database.concept import (
    MAX_RECENCY,
    Concept,
)
from ece539_adaptive_study_g17.database.database_controller import DatabaseController
from ece539_adaptive_study_g17.database.field import Field


@pytest.fixture
def session() -> Iterator[Session]:
    """Give each test its own empty in-memory database."""
    engine = create_engine("sqlite://")
    DatabaseController(engine)  # creates the tables
    with Session(engine) as session:
        yield session


def make_concept(session: Session, answers: list[tuple[int, bool]]) -> Concept:
    """Save a concept whose attempts are (response_time_ms, was_correct) pairs.

    Attempts are stored newest-first on purpose, so the test also checks that
    the summary puts them back in time order.
    """
    concept = Concept(field=Field(name="Spanish"))
    for index, (response_time_ms, was_correct) in reversed(list(enumerate(answers))):
        concept.attempts.append(
            Attempt(
                timestamp_ms=1000 * (index + 1),
                response_time_ms=response_time_ms,
                was_correct=was_correct,
            )
        )
    session.add(concept)
    session.commit()
    session.expire_all()  # force a fresh load from the database
    return concept


def test_concept_with_no_attempts_is_all_zero(session: Session) -> None:
    data = make_concept(session, []).get_evaluation_data()

    assert data.attempt_count == 0
    assert data.accuracy == 0.0
    assert data.avg_response_time_ms == 0
    assert data.recent_accuracy == 0.0
    assert data.recent_avg_response_time_ms == 0
    assert data.correct_streak == 0


def test_overall_and_recent_stats(session: Session) -> None:
    # Few attempts, so the recent window covers all of them.
    answers = [(1000, False), (2000, True), (3000, True), (4000, True)]
    expected_accuracy = 3 / 4
    expected_avg_ms = (1000 + 2000 + 3000 + 4000) // 4
    expected_streak = 3

    data = make_concept(session, answers).get_evaluation_data()

    assert data.attempt_count == len(answers)
    assert data.accuracy == expected_accuracy
    assert data.avg_response_time_ms == expected_avg_ms
    assert data.recent_accuracy == expected_accuracy
    assert data.recent_avg_response_time_ms == expected_avg_ms
    assert data.correct_streak == expected_streak


def test_recent_only_uses_newest_attempts(session: Session) -> None:
    # 20 attempts -> recent window is floor(10 * log10(21)) = 13.
    # The 7 oldest are wrong and slow; the 13 newest are right and fast.
    old_count, new_count = 7, 13
    fast_ms, slow_ms = 1000, 5000
    answers = [(slow_ms, False)] * old_count + [(fast_ms, True)] * new_count
    assert Concept._recent_window_size(len(answers)) == new_count

    data = make_concept(session, answers).get_evaluation_data()

    assert data.accuracy == new_count / len(answers)
    assert data.recent_accuracy == 1.0
    assert data.recent_avg_response_time_ms == fast_ms
    assert data.correct_streak == new_count


def test_streak_resets_on_latest_wrong_answer(session: Session) -> None:
    concept = make_concept(session, [(1000, True), (1000, True), (1000, False)])

    assert concept.get_evaluation_data().correct_streak == 0


def test_recent_window_never_exceeds_attempts() -> None:
    for attempt_count in range(30):
        assert Concept._recent_window_size(attempt_count) <= attempt_count


def test_recent_window_is_capped() -> None:
    assert Concept._recent_window_size(1_000_000) == MAX_RECENCY
