"""
Regenerate ``output/grammar.txt`` and ``output/samples.txt``.

Usage::

    python scripts/generate_outputs.py

The script is deterministic: running it twice produces byte-identical files,
which is what makes the demo video and the report reproducible.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.grammar import CFG  # noqa: E402
from src.main import write_samples  # noqa: E402

OUTPUT_DIR = ROOT / "output"


def write(path: Path, content: str) -> None:
    """Write UTF-8 content with LF line endings."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")
    print(f"  wrote {path.relative_to(ROOT)} ({len(content.splitlines())} lines)")


def generate_grammar_file() -> None:
    """output/grammar.txt -- the annotated context-free grammar."""
    grammar = CFG()
    write(OUTPUT_DIR / "grammar.txt", grammar.to_string())


def generate_samples_file() -> None:
    """Use the same sentence-only writer as the main program."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    write_samples(str(OUTPUT_DIR))
    print("  wrote output/samples.txt (one CFG sentence per line)")


def main() -> None:
    print("Regenerating output artefacts ...")
    generate_grammar_file()
    generate_samples_file()
    print("Done.")


if __name__ == "__main__":
    main()
