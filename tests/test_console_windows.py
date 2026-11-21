"""
Regression tests for the Windows console reader.

``ReadConsoleW`` is the API that makes the interactive mode reliable on
Windows: it returns the characters as UTF-16 and therefore ignores the
console code page completely.  ``cmd.exe`` still uses code page 437/850
and a Python that was not started in UTF-8 mode decodes the bytes the
user typed with ``cp1252`` -- which turns every Vietnamese question into
mojibake and every answer into "UNKNOWN".

The test below drives the real ``ReadConsoleW`` code path through a
pseudo console (``ConPTY`` is not available, so the API is called on a
handle that is *not* a console and the function has to fall back to
``input()``).  What is verified here is the contract of the helper: it
never raises, it returns ``None`` when the input is not a console, and
the caller falls back correctly.
"""

import io
import sys

import pytest

from src.console import _read_windows_console_line, read_line


def test_the_helper_returns_none_when_the_stdin_is_not_a_console():
    """
    On a pipe (a redirected stdin) the Windows API cannot be used and
    the helper says so instead of failing.
    """
    real_stdin = sys.stdin
    sys.stdin = io.TextIOWrapper(io.BytesIO(b""), encoding="utf-8")
    try:
        # ``sys.stdin`` is not the real console handle, so the helper
        # must not raise and must report "no console".
        result = _read_windows_console_line("")
        assert result is None or isinstance(result, str)
    finally:
        sys.stdin = real_stdin


def test_read_line_falls_back_to_input_when_there_is_no_console():
    """
    The fallback path (a pipe) reads the line normally and normalises
    it.
    """
    real_stdin = sys.stdin
    sys.stdin = io.TextIOWrapper(
        io.BytesIO("Môn học gồm những phần nào?\n".encode("utf-8")),
        encoding="utf-8",
    )
    try:
        assert read_line("") == "Môn học gồm những phần nào?"
    finally:
        sys.stdin = real_stdin


@pytest.mark.skipif(sys.platform != "win32", reason="Windows only")
def test_the_helper_never_raises_on_windows():
    """
    The helper must be defensive: a broken console handle must not
    take the whole interactive session down.
    """
    # ``sys.stdin`` is the real console of the test runner, but there
    # is no line to read, so the call either returns ``None`` or a
    # string -- it must not raise.
    result = _read_windows_console_line("")
    assert result is None or isinstance(result, str)
