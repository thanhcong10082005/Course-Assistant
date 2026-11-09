"""
Regenerate every artefact in ``output/``.

Usage::

    python scripts/generate_outputs.py

The script is deterministic: running it twice produces byte-identical files,
which is what makes the demo video and the report reproducible.
"""

import sys
from pathlib import Path
from typing import List, Tuple

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.grammar import CFG, generate_template_sentences  # noqa: E402

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
    """
    output/samples.txt -- the generated corpus.

    Two sections:
      1. the curated template-based questions with their intent label
      2. the sentences produced by the weighted grammar generator
    """
    lines: List[str] = []
    lines.append("# ===== GENERATED SAMPLE SENTENCES =====")
    lines.append("# Section 1: template-based questions (with their intent label)")
    lines.append("")

    for sentence, intent in generate_template_sentences():
        lines.append(f"{sentence}\t(intent={intent})")

    lines.append("")
    lines.append("# Section 2: sentences produced by the weighted CFG generator")
    lines.append("# (deterministic: seed=42)")
    lines.append("")

    grammar = CFG()
    for sentence in grammar.generate_all_sentences(max_sentences=10000, seed=42):
        lines.append(sentence)

    write(OUTPUT_DIR / "samples.txt", "\n".join(lines) + "\n")


def main() -> None:
    print("Regenerating output artefacts ...")
    generate_grammar_file()
    generate_samples_file()
    print("Done.")


if __name__ == "__main__":
    main()
