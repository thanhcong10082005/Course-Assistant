"""
Regression tests for the input of the interactive mode -- part 2.

The tests of :mod:`tests.test_console_input` cover the decoding of a
line.  The tests below cover the two mechanisms that were added
afterwards:

* the **raw byte** reading of a redirected stream: the text layer of
  Python has already decoded the bytes with a code page that can be
  wrong, and a wrong decoding is not reversible, so the bytes are read
  from the binary buffer instead;
* the repair of the **holes** the console code page leaves behind:
  cp437 cannot represent the Vietnamese letters, so "học" becomes
  "h?c" and the information is lost at the level of the operating
  system.  The word can nevertheless be restored, because the
  vocabulary of the project knows it.
"""
import io
import os
import subprocess
import sys

import pytest

from src.console import (
    _decode_stream_bytes,
    read_line,
    repair_holes,
    repair_mojibake,
    repair_raw_syllables,
    repair_typos,
)


def _console_bytes(text: str, codepage: str) -> bytes:
    """
    The bytes a console with the code page ``codepage`` produces.

    The console encodes the text with its own code page.  The code
    pages that cannot represent the Vietnamese letters turn them into
    holes -- the information is lost at the level of the operating
    system.
    """
    return text.encode(codepage, errors="replace")


def _as_latin1(data: bytes) -> str:
    """The bytes as a string, without interpreting them."""
    return data.decode("latin-1", errors="replace")


def _repaired(text: str) -> str:
    """The whole repair chain of the console."""
    text = repair_mojibake(text)
    text = repair_holes(text)
    text = repair_raw_syllables(text)
    text = repair_typos(text)
    return text


def _from_console(text: str, codepage: str) -> str:
    """The text a console with the code page ``codepage`` produces."""
    raw = _console_bytes(text, codepage)
    decoded = _decode_stream_bytes(_as_latin1(raw))
    return _repaired(decoded)


# ---------------------------------------------------------------------------
# 1. the holes of the console code page
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "codepage",
    ["cp437", "cp850", "cp1252", "cp1258"],
)
def test_the_holes_of_a_code_page_are_repaired(codepage):
    """
    A code page that cannot represent the Vietnamese letters leaves
    holes: "học" becomes "h?c".  The word is restored from the
    vocabulary of the project.
    """
    original = "Môn học gồm những phần nào?"
    raw = _console_bytes(original, codepage)
    assert b"?" in raw, raw
    assert _from_console(original, codepage) == original


def test_several_holes_in_one_word_are_repaired():
    """A word with several holes is repaired as well."""
    assert repair_holes("Ch??ng 4 nói về gì?") == "Chương 4 nói về gì?"


def test_a_hole_and_a_typo_are_repaired_together():
    """
    A typo and a hole in the same word are both repaired.

    "thph?n" is the word "phần" with two extra letters *and* a lost
    accent: the hole repair finds the word and the typo repair removes
    the extra letters.
    """
    assert _repaired("Môn học gồm những thph?n nào?") == (
        "Môn học gồm những phần nào?"
    )


def test_a_correct_word_is_never_touched():
    original = "Môn học gồm những phần nào?"
    assert repair_holes(original) == original
    assert _repaired(original) == original


def test_the_candidates_of_an_ambiguous_hole_are_all_reported():
    """
    A hole that several words could fill is reported with all of them.

    A wrong guess would be worse than no guess at all: the user would
    get an answer about a completely different subject.  The candidates
    are therefore collected first, and the repair only happens when
    exactly one of them fits the sentence.
    """
    from src.console import _hole_candidates

    candidates = _hole_candidates("ph?n")
    assert "phần" in candidates
    # "phân" fits as well -- the corpus of the project decides.
    assert "phân" in candidates


def test_the_punctuation_is_not_a_hole():
    """The question mark of the sentence is never eaten."""
    assert repair_holes("Chương 4 nói về gì?").endswith("?")


# ---------------------------------------------------------------------------
# 2. the raw byte reading of a redirected stream
# ---------------------------------------------------------------------------
def test_a_utf8_pipe_is_decoded_as_utf8():
    raw = "Môn học gồm những phần nào?".encode("utf-8").decode("latin-1")
    assert _decode_stream_bytes(raw) == "Môn học gồm những phần nào?"


def test_a_console_pipe_is_decoded_as_the_console_code_page():
    """
    A line that was written with the code page of the console is
    decoded with it.

    The bytes of "Môn học gồm những phần nào?" are written with cp437
    by the console, and the reader has to find the right code page on
    its own.
    """
    original = "Môn học gồm những phần nào?"
    raw = _console_bytes(original, "cp437")
    decoded = _decode_stream_bytes(_as_latin1(raw))
    assert _repaired(decoded) == original


def test_read_line_reads_the_raw_bytes_of_a_pipe():
    """
    The bytes of a redirected stream are read from the binary buffer.

    The text layer would have decoded them with the code page of the
    environment, and a wrong decoding cannot be undone.
    """
    real_stdin = sys.stdin
    payload = "Môn học gồm những phần nào?\n".encode("utf-8")
    sys.stdin = io.TextIOWrapper(io.BytesIO(payload), encoding="cp1252")
    try:
        assert read_line("") == "Môn học gồm những phần nào?"
    finally:
        sys.stdin = real_stdin


def test_read_line_returns_none_on_eof_of_a_pipe():
    real_stdin = sys.stdin
    sys.stdin = io.TextIOWrapper(io.BytesIO(b""), encoding="utf-8")
    try:
        assert read_line("") is None
    finally:
        sys.stdin = real_stdin


# ---------------------------------------------------------------------------
# 3. the whole pipeline
# ---------------------------------------------------------------------------
def _run_interactive(payload: bytes) -> str:
    """The output of the interactive mode for the given input."""
    environment = dict(os.environ)
    environment["PYTHONIOENCODING"] = "utf-8"

    result = subprocess.run(
        [sys.executable, "-m", "src.main", "--mode", "interactive"],
        input=payload,
        capture_output=True,
        env=environment,
    )
    return result.stdout.decode("utf-8", errors="replace")


@pytest.mark.parametrize(
    "codepage",
    ["utf-8", "cp437", "cp850", "cp1252"],
)
def test_the_question_is_understood_in_every_encoding(codepage):
    """
    The reported question reaches the right intent whatever the
    encoding of the console is.

    This is the contract of the bug report: the same question must
    give the same answer whether it was pasted or typed, and whatever
    the code page of the console is.
    """
    original = "Môn học gồm những phần nào?"
    output = _run_interactive(_console_bytes(original + "\n", codepage))
    assert "GET_COURSE_INFO" in output, output
    assert "UNKNOWN" not in output, output


@pytest.mark.parametrize(
    "codepage",
    ["utf-8", "cp437", "cp850", "cp1252"],
)
def test_the_typo_is_understood_in_every_encoding(codepage):
    """The reported typo is repaired in every encoding as well."""
    original = "Môn học gồm những thphần nào?"
    output = _run_interactive(_console_bytes(original + "\n", codepage))
    assert "GET_COURSE_INFO" in output, output
    assert "UNKNOWN" not in output, output
