"""
Regression tests for the interactive-mode input robustness.

The bugs these tests pin down were reported by the team:

* *"khi copy paste thì chạy, còn gõ từ từ thì không chạy"* -- the same
  question gave two different answers depending on how it reached the
  program;
* *"mấy câu như Môn học gồm những thphần nào? ngoài terminal thì bình
  thường, log trong docker thì ra lung tung lắm"*.

The root cause was the **decoding of the input**, not the analysis:

``cmd.exe`` still uses code page 437/850 and a Python that was not
started in UTF-8 mode decodes the bytes the user typed with ``cp1252``.
The Vietnamese text then becomes mojibake ("MÃ´n há»­c"), the lexicon
recognises no surface form any more, and the analyzer answers
``UNKNOWN``.

The fixes live in :mod:`src.console`:

1. on a real Windows console the line is read with ``ReadConsoleW``
   (UTF-16, immune to the code page),
2. a mojibake text is repaired,
3. the invisible control characters a terminal leaves behind are
   removed,
4. a syllable the Vietnamese input method left in its "raw" form gets
   its tone mark back.
"""

import io
import sys

import pytest

from src.console import (
    read_line,
    repair_mojibake,
    repair_raw_syllables,
    repair_typos,
    strip_control_characters,
)


# ---------------------------------------------------------------------------
# 1. control characters
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "dirty",
    [
        "Môn học gồm những phần nào?\x1b",
        "Môn học gồm những phần nào?\x7f",
        "Môn học gồm những phần nào?\x08",
        "Môn học gồm những phần nào?\x1b[0m",
        "\x1b[200~Môn học gồm những phần nào?\x1b[201~",
        "Môn học gồm những phần nào?\r",
        "Môn học gồm những phần nào?\x00",
        "Môn học gồm những phần nào?﻿",
    ],
)
def test_control_characters_are_removed(dirty):
    """The invisible characters a terminal leaves behind are dropped."""
    assert strip_control_characters(dirty) == "Môn học gồm những phần nào?"


def test_a_clean_line_is_untouched():
    assert strip_control_characters("Môn học gồm những phần nào?") == (
        "Môn học gồm những phần nào?"
    )


@pytest.mark.parametrize(
    "text",
    [
        "deadline L.O.2.5",
        "a-b",
        "2024-2025",
        "Bài tập lớn #1",
        "x y z 0123",
        "normal text",
    ],
)
def test_the_printable_characters_survive(text):
    """
    Only the *invisible* characters may be removed.

    A character class written with literal characters can accidentally
    build a range that swallows the printable ASCII between the two
    ends ("-" and U+200F would have removed everything in between).
    """
    assert strip_control_characters(text) == text


# ---------------------------------------------------------------------------
# 2. mojibake repair
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("codepage", ["cp437", "cp850", "cp866"])
def test_mojibake_is_repaired(codepage):
    """
    A question that was decoded with the wrong code page is restored.

    This is the exact mechanism of the reported bug: the bytes of the
    UTF-8 text are decoded with the console code page, and the result
    no longer matches any lexicon surface.

    Only the code pages that map **all 256 byte values** can be repaired
    perfectly, because the others drop a few bytes on the way in (for
    cp1252 the bytes 0x81, 0x8D, 0x8F, 0x90 and 0x9D have no
    counterpart).  ``cp437`` and ``cp850`` -- the code pages of the
    Windows console -- are byte preserving, and they are repaired
    exactly.
    """
    original = "Môn học gồm những phần nào?"
    mojibake = original.encode("utf-8").decode(codepage, errors="replace")
    assert mojibake != original
    repaired = repair_mojibake(mojibake)
    assert repaired == original


@pytest.mark.parametrize("codepage", ["cp1252", "cp1258"])
def test_a_lossy_mojibake_is_repaired_by_recovering_the_lost_bytes(codepage):
    """
    cp1252 cannot represent five byte values (0x81, 0x8D, 0x8F, 0x90,
    0x9D), so a text decoded with it has *already* lost information
    before the repair even starts: the console replaced those bytes
    with U+FFFD.

    The bytes are nevertheless recovered, because there are only five
    candidates and only one of them produces a sentence made of known
    Vietnamese words ("học" instead of "hềc").  The vocabulary of the
    project decides -- see :func:`src.console._recover_lost_bytes`.

    This is still only the safety net for a redirected stdin: on a real
    Windows console the line is read with ``ReadConsoleW`` (see
    :func:`src.console.read_line`), which never goes through a code
    page at all.
    """
    original = "Môn học gồm những phần nào?"
    mojibake = original.encode("utf-8").decode(codepage, errors="replace")
    # The information really was lost: the replacement character is
    # already in the string.
    assert "�" in mojibake
    # The repair brings it back all the same.
    assert repair_mojibake(mojibake) == original


def test_a_correct_text_is_not_modified():
    original = "Môn học gồm những phần nào?"
    assert repair_mojibake(original) == original


def test_english_text_is_not_modified():
    assert repair_mojibake("Hello world") == "Hello world"


def test_the_mojibake_really_would_break_the_pipeline():
    """
    The mojibake is *not* harmless: without the repair the analyzer
    answers UNKNOWN.  This test documents why the repair matters.
    """
    from src.semantic import SemanticAnalyzer

    analyzer = SemanticAnalyzer()
    original = "Môn học gồm những phần nào?"
    mojibake = original.encode("utf-8").decode("cp437", errors="replace")

    assert analyzer.analyze(mojibake).intent.value == "UNKNOWN"
    assert analyzer.analyze(repair_mojibake(mojibake)).intent.value == (
        "GET_COURSE_INFO"
    )


# ---------------------------------------------------------------------------
# 3. raw syllables (Vietnamese input method)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "raw,expected",
    [
        ("Môn hoc gom nhung phan nao?", "Môn học gồm những phần nào?"),
        ("mon hoc", "môn học"),
        ("tuan 3 hoc gi", "tuần 3 học gì"),
        ("bai tap lon yeu cau xay dung nhung gi",
         "bài tập lớn yêu cầu xây dựng những gì"),
    ],
)
def test_raw_syllables_get_their_tone_mark(raw, expected):
    """
    Telex needs a second key press to drop the tone mark.  When the user
    presses Enter too early the syllable stays raw.
    """
    assert repair_raw_syllables(raw) == expected


def test_an_untouched_word_is_not_corrupted():
    """A word the lexicon does not know keeps its spelling."""
    assert repair_raw_syllables("xyzzy") == "xyzzy"


def test_a_correct_text_is_not_modified():
    original = "Môn học gồm những phần nào?"
    assert repair_raw_syllables(original) == original


# ---------------------------------------------------------------------------
# 3b. typos typed inside a word
# ---------------------------------------------------------------------------
def test_a_typo_inside_a_word_is_repaired():
    """
    "thphần" -> "phần".

    The extra letters were typed inside the word; the intent rules need
    the phrase "gồm những phần" to recognise the question.
    """
    assert repair_typos("Môn học gồm những thphần nào?") == (
        "Môn học gồm những phần nào?"
    )


def test_a_correct_word_is_not_modified():
    assert repair_typos("Môn học gồm những phần nào?") == (
        "Môn học gồm những phần nào?"
    )


def test_an_unknown_word_is_not_modified():
    """A word that is simply unknown keeps its spelling."""
    assert repair_typos("xyzzy abc asdkjh") == "xyzzy abc asdkjh"


def test_a_short_extra_prefix_is_not_repaired():
    """
    The repair is conservative: the extra letters must be at most two
    and the word they hide must be a real Vietnamese word.
    """
    # Three extra letters -> no repair.
    assert repair_typos("xyzhphần") == "xyzhphần"


def test_the_whole_question_gets_the_same_answer():
    """
    The question with the typo and the question without it give exactly
    the same answer.
    """
    from src.main import CourseAssistant

    assistant = CourseAssistant()
    clean, _ = assistant.process_dialogue("Môn học gồm những phần nào?", {})
    fixed, _ = assistant.process_dialogue(
        repair_typos("Môn học gồm những thphần nào?"), {}
    )
    assert clean == fixed


# ---------------------------------------------------------------------------
# 4. read_line
# ---------------------------------------------------------------------------
def _read_with(payload: str, encoding: str = "utf-8"):
    """Feed ``payload`` to :func:`read_line` through a fake stdin."""
    real_stdin = sys.stdin
    sys.stdin = io.TextIOWrapper(
        io.BytesIO(payload.encode("utf-8") + b"\n"), encoding=encoding
    )
    try:
        return read_line("")
    finally:
        sys.stdin = real_stdin


def test_read_line_returns_a_clean_question():
    assert _read_with("Môn học gồm những phần nào?") == (
        "Môn học gồm những phần nào?"
    )


def test_read_line_strips_the_control_characters():
    assert _read_with("Môn học gồm những phần nào?\x1b[0m\x7f") == (
        "Môn học gồm những phần nào?"
    )


def test_read_line_repairs_a_mojibake_line():
    mojibake = "Môn học gồm những phần nào?".encode("utf-8").decode(
        "cp437", errors="replace"
    )
    line = _read_with(mojibake)
    assert line is not None
    assert "gồm" in line.lower()


def test_read_line_restores_the_raw_syllables():
    assert _read_with("Môn hoc gom nhung phan nao?") == (
        "Môn học gồm những phần nào?"
    )


def test_read_line_returns_none_on_eof():
    real_stdin = sys.stdin
    sys.stdin = io.TextIOWrapper(io.BytesIO(b""), encoding="utf-8")
    try:
        assert read_line("") is None
    finally:
        sys.stdin = real_stdin


# ---------------------------------------------------------------------------
# 5. the whole pipeline
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "question",
    [
        "Môn NLP gồm những phần nào?",
        "Môn học gồm những phần nào?",
        "Môn học gồm những thphần nào?",
        "Môn học gồm những phần nao?",
    ],
)
def test_the_question_gets_understood(question):
    """
    Every variant of the reported question reaches the right intent.

    This is the contract the team asked for: the same question must
    give the same answer whether it was pasted or typed.
    """
    from src.main import CourseAssistant

    assistant = CourseAssistant()
    answer, context = assistant.process_dialogue(question, {})
    assert context["last_intent"] == "GET_COURSE_INFO", question
    assert "phần chính" in answer or "Môn Xử lý Ngôn ngữ Tự nhiên" in answer


def test_the_mojibake_question_gives_the_same_answer_as_the_clean_one():
    """
    The pasted question and the typed question give the *same* answer.
    """
    from src.main import CourseAssistant

    assistant = CourseAssistant()
    clean, _ = assistant.process_dialogue("Môn học gồm những phần nào?", {})
    mojibake = "Môn học gồm những phần nào?".encode("utf-8").decode(
        "cp437", errors="replace"
    )
    dirty, _ = assistant.process_dialogue(repair_mojibake(mojibake), {})
    assert clean == dirty


# ---------------------------------------------------------------------------
# 6. suggestions
# ---------------------------------------------------------------------------
def test_an_unknown_question_gets_a_suggestion():
    """
    A question the assistant does not understand points to the questions
    it *does* understand.
    """
    from src.knowledge_base import KnowledgeBase

    kb = KnowledgeBase()
    suggestions = kb.suggest("Môn học gồm những thphần nào?")
    assert suggestions
    assert "Môn học gồm những phần nào?" in suggestions


def test_a_meaningless_question_gets_no_suggestion():
    """A wrong suggestion is worse than no suggestion."""
    from src.knowledge_base import KnowledgeBase

    kb = KnowledgeBase()
    assert kb.suggest("xyzzy qwerty asdfgh") == []


def test_the_unknown_answer_mentions_the_suggestions():
    from src.knowledge_base import KnowledgeBase

    kb = KnowledgeBase()
    answer = kb.unknown_answer_with_suggestions("Môn học gồm những thphần nào?")
    assert "Môn học gồm những phần nào?" in answer
