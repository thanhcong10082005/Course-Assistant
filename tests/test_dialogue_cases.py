"""
Tests for the dialogue / local discourse context component.

The dialogue behaviour is validated against the official sample dialogues in
``tests/data/dialogues.txt`` plus the context-dependent queries of the
official test set.

Until the real :class:`~src.dialogue.DialogueManager` is wired into the
pipeline these tests describe the *target* behaviour; they are expected to
fail before WP6 and to pass afterwards.  The failures are registered in
``tests/known_issues.py`` so the quality gate stays green.
"""

import pytest

from tests.conftest import DIALOGUES


# ---------------------------------------------------------------------------
# Reference cases taken from the official sample dialogues
# ---------------------------------------------------------------------------
DIALOGUE_CASES = [
    {
        "id": "DIALOGUE_01",
        "turns": [
            ("Tuần 3 học gì?", "GET_SCHEDULE", {"week": "WEEK_03"}),
            (
                "Tài liệu của chương này là gì?",
                "GET_RESOURCE",
                {"chapter": "CH03"},
            ),
        ],
    },
    {
        "id": "DIALOGUE_02",
        "turns": [
            ("Chương 4 nói về gì?", "GET_TOPIC", {"chapter": "CH04"}),
            (
                "Nó có liên quan đến parsing không?",
                "GET_TOPIC",
                {"chapter": "CH04"},
            ),
        ],
    },
    {
        "id": "DIALOGUE_03",
        "turns": [
            (
                "Bài tập lớn có phần parser không?",
                "GET_ASSIGNMENT",
                {"assignment": "BTL01"},
            ),
            ("Phần này cần xuất file gì?", "GET_ASSIGNMENT", {"part": "PART_I"}),
        ],
    },
    {
        "id": "DIALOGUE_04",
        "turns": [
            ("Chương 11 có hỏi đáp không?", "GET_TOPIC", {"chapter": "CH11"}),
            ("Còn chương sau?", "GET_TOPIC", {"chapter": "CH12"}),
        ],
    },
    {
        "id": "DIALOGUE_05",
        "turns": [
            ("L.O.2.5 học về gì?", "GET_LO", {"lo": "LO2.5"}),
            ("Nội dung này nằm ở chương nào?", "GET_TOPIC", {"lo": "LO2.5"}),
        ],
    },
]


def test_dialogue_sample_file_is_present():
    """The official dialogue fixture must be bundled with the tests."""
    assert DIALOGUES.exists(), "tests/data/dialogues.txt is missing"
    content = DIALOGUES.read_text(encoding="utf-8")
    assert "DIALOGUE 01" in content
    assert "DIALOGUE 05" in content


# ---------------------------------------------------------------------------
# DialogueManager in isolation -- these tests describe the manager contract
# and do not depend on the pipeline wiring (WP6).
# ---------------------------------------------------------------------------
@pytest.fixture
def manager():
    from src.dialogue import DialogueManager

    return DialogueManager()


def test_manager_starts_empty(manager):
    summary = manager.get_state_summary()
    assert summary["turn"] == 0
    assert summary["last_chapter"] is None
    assert summary["last_topic"] is None


def test_manager_updates_context(manager):
    manager.update_context("GET_TOPIC", {"chapter": "CH04"}, "Chương 4 nói về gì?")

    summary = manager.get_state_summary()
    assert summary["turn"] == 1
    assert summary["last_intent"] == "GET_TOPIC"
    assert summary["last_chapter"] == "CH04"


def test_manager_reset_clears_context(manager):
    manager.update_context("GET_TOPIC", {"chapter": "CH04"}, "Chương 4 nói về gì?")
    manager.reset()

    summary = manager.get_state_summary()
    assert summary["turn"] == 0
    assert summary["last_chapter"] is None


def test_manager_resolves_demonstrative_reference(manager):
    """'phần này' must be resolved against the discourse state."""
    manager.update_context("GET_ASSIGNMENT", {"assignment": "BTL01"}, "Bài tập lớn")

    resolved = manager.resolve_reference("Phần này cần xuất file gì?")
    assert resolved is not None
    assert "BTL01" in str(resolved)


def test_manager_history_is_recorded(manager):
    manager.update_context("GET_TOPIC", {"chapter": "CH04"}, "Chương 4 nói về gì?")
    manager.update_context("GET_TOPIC", {"chapter": "CH05"}, "Chương 5 nói về gì?")

    history = manager.get_history()
    assert len(history) == 2


# ---------------------------------------------------------------------------
# Pipeline-level dialogue behaviour (requires WP6 wiring)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "case", DIALOGUE_CASES, ids=[c["id"] for c in DIALOGUE_CASES]
)
def test_dialogue_resolves_reference(case, fresh_assistant):
    """
    Each turn of the sample dialogues must resolve its contextual reference
    against the discourse state built by the preceding turns.
    """
    assistant = fresh_assistant
    for index, (query, expected_intent, expected_entities) in enumerate(case["turns"]):
        answer, _context = assistant.process_dialogue(query)

        result = assistant.process_query(query)
        assert result["intent"] == expected_intent, (
            f"{case['id']} turn {index + 1}: '{query}' -> "
            f"{result['intent']} (expected {expected_intent})"
        )
        for key, value in expected_entities.items():
            assert result["entities"].get(key) == value, (
                f"{case['id']} turn {index + 1}: '{query}' -> "
                f"{result['entities']} (expected {key}={value})"
            )


def test_context_dependent_without_context_asks_for_clarification(fresh_assistant):
    """
    A context-dependent query issued as the very first turn cannot be
    resolved -- the system must ask instead of guessing.
    """
    assistant = fresh_assistant
    result = assistant.process_query("Nó có liên quan đến parsing không?")

    assert result["intent"] == "CONTEXT_DEPENDENT"
    answer = result["answer"].lower()
    assert "trước" in answer or "ngữ cảnh" in answer or "chương" in answer
