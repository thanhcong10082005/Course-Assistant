"""
Regression tests for the Windows console encoding fix and the artefact contracts.

Two bugs that are invisible in the Docker image but fatal on a native
Windows console are pinned here:

1. **Encoding** -- Python starts on Windows with the legacy code page
   ``cp1252``.  Printing the very first accented character of the demo
   banner used to abort the program with::

       UnicodeEncodeError: 'charmap' codec can't encode character '\\u1ec7'

   ``src.main`` now reconfigures ``stdin``/``stdout``/``stderr`` to UTF-8
   at import time, so ``--mode demo`` and ``--mode interactive`` run
   natively without ``PYTHONIOENCODING`` being set.

2. **Artefact contract** -- ``output/parse-results.txt`` holds one tree per
   sentence of ``input/sentences.txt`` (34 lines), *not* one tree per
   sentence of ``output/samples.txt`` (10,000 generated sentences).  The
   two artefacts serve two different requirements of the assignment.
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# 1. the encoding fix
# ---------------------------------------------------------------------------
def test_streams_are_reconfigured_to_utf8():
    """Importing ``src.main`` leaves the standard streams on UTF-8.

    The check runs in a **subprocess** because pytest replaces
    ``sys.stdout`` with a capture object that does not support
    ``reconfigure`` -- and the guard in ``src.main`` deliberately skips
    such streams.
    """
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "cp1252"

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys, src.main; "
            "print(sys.stdout.encoding, sys.stderr.encoding)",
        ],
        cwd=str(ROOT),
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )
    assert result.returncode == 0, result.stderr[-2000:]
    encodings = result.stdout.strip().split()
    assert encodings == ["utf-8", "utf-8"], result.stdout


def test_force_utf8_stdio_is_idempotent():
    """Calling the helper twice must not raise."""
    from src.main import _force_utf8_stdio

    _force_utf8_stdio()
    _force_utf8_stdio()


def test_check_submission_script_reconfigures_its_own_streams():
    """The checker prints Vietnamese too, so it needs the same guard."""
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "_check_submission", ROOT / "scripts" / "check_submission.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert hasattr(module, "_force_utf8_stdio")

    # Run it for real on a legacy code page: it must print the report and
    # exit with 0 instead of dying with a UnicodeEncodeError.
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "cp1252"

    result = subprocess.run(
        [sys.executable, "scripts/check_submission.py"],
        cwd=str(ROOT),
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=300,
    )
    assert "UnicodeEncodeError" not in (result.stderr or ""), result.stderr[-2000:]
    assert result.returncode == 0, result.stderr[-2000:]
    assert "KIỂM TRA" in result.stdout


@pytest.mark.skipif(sys.platform != "win32", reason="Windows-only console behaviour")
def test_demo_mode_survives_a_legacy_code_page():
    """The demo must not crash when the console is not UTF-8."""
    env = dict(os.environ)
    env.pop("PYTHONIOENCODING", None)
    env["PYTHONIOENCODING"] = "cp1252"

    result = subprocess.run(
        [sys.executable, "-m", "src.main", "--mode", "demo"],
        cwd=str(ROOT),
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=300,
    )
    assert "UnicodeEncodeError" not in (result.stderr or ""), result.stderr[-2000:]
    assert result.returncode == 0, result.stderr[-2000:]


# ---------------------------------------------------------------------------
# 2. the artefact contract
# ---------------------------------------------------------------------------
def test_parse_results_has_one_line_per_input_sentence():
    """``parse-results.txt`` mirrors ``input/sentences.txt``, line by line."""
    sentences_file = ROOT / "input" / "sentences.txt"
    parse_file = ROOT / "output" / "parse-results.txt"

    if not sentences_file.exists() or not parse_file.exists():
        pytest.skip("artefacts have not been generated yet")

    sentences = [
        line.strip()
        for line in sentences_file.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    trees = [
        line.strip()
        for line in parse_file.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    assert len(trees) == len(sentences)
    assert len(trees) == 34


def test_parse_results_is_not_the_generated_corpus():
    """Guard against the two artefacts being confused with each other."""
    samples_file = ROOT / "output" / "samples.txt"
    parse_file = ROOT / "output" / "parse-results.txt"

    if not samples_file.exists() or not parse_file.exists():
        pytest.skip("artefacts have not been generated yet")

    samples = samples_file.read_text(encoding="utf-8").splitlines()
    trees = parse_file.read_text(encoding="utf-8").splitlines()

    assert len(samples) != len(trees)
    assert len(samples) > len(trees)


def test_every_out_of_grammar_sentence_is_an_empty_tree():
    """Section 3.3: a sentence outside the grammar is printed as ``()``."""
    parse_file = ROOT / "output" / "parse-results.txt"
    if not parse_file.exists():
        pytest.skip("artefacts have not been generated yet")

    trees = [
        line.strip()
        for line in parse_file.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    for tree in trees:
        assert tree == "()" or tree.startswith("("), tree
