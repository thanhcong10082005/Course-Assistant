"""
Check that the submission package is complete.

The script verifies that every file the assignment asks for is present and
that the artefacts are not empty.  It is meant to be run **before** the
package is handed in::

    python scripts/check_submission.py

The exit code is ``0`` when every check passes and ``1`` otherwise, so the
script can be used in a CI pipeline.
"""

from __future__ import annotations

import os
import sys
from typing import List, Tuple

# The root of the repository (the parent of ``scripts/``).
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# The directories that have to be part of the package.
REQUIRED_DIRS = [
    "src",
    "data",
    "models",
    "input",
    "output",
    "tests",
    "docs",
]

# The files that have to be part of the package.
REQUIRED_FILES = [
    "README.md",
    "Dockerfile",
    "requirements.txt",
    "pytest.ini",
]

# The nine artefacts the assignment asks for.
REQUIRED_OUTPUTS = [
    "grammar.txt",
    "samples.txt",
    "parse-results.txt",
    "semantic.txt",
    "intent-entity.txt",
    "query.txt",
    "answer.txt",
    "dialogue.txt",
    "evaluation.txt",
]

# The handover documents that help the team write the report.
#
# The four team-only documents (DIAGRAM / HANDOVER / DEMO_SCRIPT /
# KIEM_TRA_BAN_GIAO) are deliberately **not** part of this package: they are
# distributed to the team separately.  Only the documents that belong to the
# deliverable are checked here.
REQUIRED_DOCS = [
    "REPORT.md",
    "baseline.txt",
]

# The team-only documents, distributed to the team outside the package.
EXTERNAL_DOCS = [
    "DIAGRAM.md",
    "HANDOVER.md",
    "DEMO_SCRIPT.md",
    "KIEM_TRA_BAN_GIAO.md",
]

# The source modules of the system.
REQUIRED_MODULES = [
    "src/preprocessing.py",
    "src/grammar.py",
    "src/parser.py",
    "src/lexicon.py",
    "src/semantic.py",
    "src/knowledge_base.py",
    "src/dialogue.py",
    "src/evaluation.py",
    "src/main.py",
]

# The minimum size (in bytes) of a non empty artefact.
MIN_OUTPUT_BYTES = 200


def _check(results: List[Tuple[bool, str]], ok: bool, message: str) -> None:
    results.append((ok, message))


def check_directories(results: List[Tuple[bool, str]]) -> None:
    """Every required directory exists."""
    for name in REQUIRED_DIRS:
        path = os.path.join(ROOT, name)
        _check(results, os.path.isdir(path), f"thư mục  {name}/")


def check_files(results: List[Tuple[bool, str]]) -> None:
    """Every required file exists."""
    for name in REQUIRED_FILES:
        path = os.path.join(ROOT, name)
        _check(results, os.path.isfile(path), f"tệp     {name}")


def check_modules(results: List[Tuple[bool, str]]) -> None:
    """Every source module exists."""
    for name in REQUIRED_MODULES:
        path = os.path.join(ROOT, name.replace("/", os.sep))
        _check(results, os.path.isfile(path), f"module  {name}")


def check_outputs(results: List[Tuple[bool, str]]) -> None:
    """Every artefact exists and is not empty."""
    for name in REQUIRED_OUTPUTS:
        path = os.path.join(ROOT, "output", name)
        if not os.path.isfile(path):
            _check(results, False, f"output  output/{name} (thiếu)")
            continue
        size = os.path.getsize(path)
        _check(
            results,
            size >= MIN_OUTPUT_BYTES,
            f"output  output/{name} ({size} bytes)",
        )


def check_docs(results: List[Tuple[bool, str]]) -> None:
    """Every deliverable document exists."""
    for name in REQUIRED_DOCS:
        path = os.path.join(ROOT, "docs", name)
        _check(results, os.path.isfile(path), f"docs    docs/{name}")


def check_external_docs(results: List[Tuple[bool, str]]) -> None:
    """The team-only documents are *not* shipped inside the package.

    They are distributed to the team separately, so their absence from the
    package is the correct state - this check makes that explicit instead of
    silent, so nobody wonders where the diagrams went.
    """
    for name in EXTERNAL_DOCS:
        path = os.path.join(ROOT, "docs", name)
        _check(
            results,
            not os.path.isfile(path),
            f"docs    docs/{name} (gửi riêng cho nhóm, không nằm trong gói)",
        )


def clean_caches() -> None:
    """Remove every ``__pycache__`` directory and every ``.pyc`` file."""
    for dirpath, dirnames, filenames in os.walk(ROOT, topdown=False):
        if ".git" in dirpath:
            continue
        for filename in filenames:
            if filename.endswith(".pyc"):
                try:
                    os.remove(os.path.join(dirpath, filename))
                except OSError:
                    pass
        for dirname in dirnames:
            if dirname == "__pycache__":
                cache = os.path.join(dirpath, dirname)
                try:
                    os.rmdir(cache)
                except OSError:
                    # The directory is not empty (a leftover sub-directory):
                    # remove it recursively instead.
                    import shutil

                    shutil.rmtree(cache, ignore_errors=True)


def check_no_cache(results: List[Tuple[bool, str]]) -> None:
    """No ``__pycache__`` directory is left in the package."""
    found = []
    for dirpath, dirnames, _filenames in os.walk(ROOT):
        if ".git" in dirpath:
            continue
        for dirname in dirnames:
            if dirname == "__pycache__":
                found.append(os.path.relpath(os.path.join(dirpath, dirname), ROOT))
    _check(
        results,
        not found,
        "sạch    không còn __pycache__"
        if not found
        else f"sạch    tìm thấy __pycache__: {found}",
    )


def check_no_cache_files(results: List[Tuple[bool, str]]) -> None:
    """No ``.pyc`` file is left in the package."""
    found = []
    for dirpath, _dirnames, filenames in os.walk(ROOT):
        if ".git" in dirpath:
            continue
        for filename in filenames:
            if filename.endswith(".pyc"):
                found.append(
                    os.path.relpath(os.path.join(dirpath, filename), ROOT)
                )
    _check(
        results,
        not found,
        "sạch    không còn file .pyc"
        if not found
        else f"sạch    tìm thấy {len(found)} file .pyc",
    )


def check_lexicon(results: List[Tuple[bool, str]]) -> None:
    """The lexicon is present and holds a reasonable number of surfaces."""
    path = os.path.join(ROOT, "models", "lexicon.json")
    if not os.path.isfile(path):
        _check(results, False, "lexicon models/lexicon.json (thiếu)")
        return
    try:
        import json

        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        count = sum(
            len(value) for value in data.values()
            if isinstance(value, dict)
        )
        _check(
            results,
            count >= 100,
            f"lexicon {count} bề mặt từ trong models/lexicon.json",
        )
    except Exception as exc:  # pragma: no cover - defensive
        _check(results, False, f"lexicon không đọc được: {exc}")


def main() -> int:
    results: List[Tuple[bool, str]] = []

    print("=" * 70)
    print("KIỂM TRA GÓI NỘP BÀI - COURSE ASSISTANT")
    print("=" * 70)
    print(f"Thư mục gốc: {ROOT}")
    print("-" * 70)

    # The caches are removed *first*: they are never part of the package
    # and would otherwise make the last two checks fail.
    clean_caches()

    check_directories(results)
    check_files(results)
    check_modules(results)
    check_outputs(results)
    check_docs(results)
    check_external_docs(results)
    check_lexicon(results)
    check_no_cache(results)
    check_no_cache_files(results)

    for ok, message in results:
        print(f"  [{'OK' if ok else '!!'}] {message}")

    failed = [message for ok, message in results if not ok]
    print("-" * 70)
    if failed:
        print(f"FAILED: {len(failed)} / {len(results)} kiểm tra không đạt.")
        for message in failed:
            print(f"  - {message}")
        print("=" * 70)
        return 1

    print(f"ALL CHECKS PASSED ({len(results)} / {len(results)})")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
