"""
Measure and report the current quality metrics of the Course Assistant.

Usage::

    python scripts/baseline.py            # print to stdout
    python scripts/baseline.py --out docs/baseline.txt

The script reports three families of metrics:

1. **Official test set** (``tests/data/sample_queries.txt``, 34 queries)
   -- intent accuracy, entity accuracy and the combined accuracy.
2. **Parser quality** -- how many sentences are handled by the strict
   Earley chart parser versus the pattern-based fallback.
3. **Sentence generation** -- how many sentences the grammar produces and
   how many of them look like a well-formed Vietnamese question.
"""

import argparse
import io
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _safe_print(text: str) -> None:
    """Print without blowing up on consoles that cannot encode Vietnamese."""
    try:
        print(text)
    except UnicodeEncodeError:
        encoding = sys.stdout.encoding or "ascii"
        safe = text.encode(encoding, errors="replace").decode(encoding, errors="replace")
        print(safe)


ENTITY_ALIASES = {
    "CO3085": {"course": ["CO3085", "NLP"]},
    "MIDTERM": {"attribute": ["midterm_duration"]},
    "FINAL": {"attribute": ["final_duration"]},
    "OUT_OF_SCOPE": {"scope": ["OUT_OF_SCOPE"]},
}


def entity_matches(expected, entities) -> bool:
    if expected in ENTITY_ALIASES:
        spec = ENTITY_ALIASES[expected]
        for key, values in spec.items():
            if key == "scope":
                if entities.get("scope") in values:
                    return True
                continue
            if entities.get(key) in values:
                return True
        return False
    return expected in str(entities)


def entity_matches_strict(expected, entities) -> bool:
    """Raw substring match -- no alias table. Kept as a second, harsher metric."""
    return expected in str(entities)


def evaluate_official(assistant, cases):
    intent_ok = 0
    entity_ok = 0
    entity_ok_strict = 0
    combined_ok = 0
    failures = []

    for case in cases:
        result = assistant.process_query(case["query"])
        i_ok = result["intent"] == case["expected_intent"]
        e_ok = True
        if case["expected_entity"]:
            e_ok = entity_matches(case["expected_entity"], result["entities"])
            entity_ok_strict += entity_matches_strict(
                case["expected_entity"], result["entities"]
            )
        else:
            entity_ok_strict += 1

        intent_ok += i_ok
        entity_ok += e_ok
        combined_ok += i_ok and e_ok

        if not (i_ok and e_ok):
            failures.append(
                f"  [{case['id']}] {case['query']}\n"
                f"      expected: {case['expected_intent']} / {case['expected_entity']}\n"
                f"      actual  : {result['intent']} / {result['entities']}"
            )

    total = len(cases)
    return {
        "total": total,
        "intent_ok": intent_ok,
        "entity_ok": entity_ok,
        "entity_ok_strict": entity_ok_strict,
        "combined_ok": combined_ok,
        "failures": failures,
    }


def evaluate_parser(parser, cases):
    strict = 0
    fallback = 0
    failure = 0

    for case in cases:
        text = case["query"]
        parser.tokens = parser.tokenize_input(text)
        parser.current_pos = 0
        parser.errors = []
        tree = parser._parse_question()
        if tree and parser.current_pos == len(parser.tokens):
            strict += 1
            continue
        if parser._parse_fallback(text):
            fallback += 1
        else:
            failure += 1

    return {"strict": strict, "fallback": fallback, "failure": failure}


def evaluate_generation(grammar):
    sentences = grammar.generate_all_sentences(max_sentences=10000)
    underscore = sum(1 for s in sentences if "_" in s)
    wh_phrase = sum(1 for s in sentences if "WH_PHRASE" in s)
    # A generated sentence must not open with a bare verb.
    verb_like = {
        "mấy", "tra", "xem", "tìm", "muốn", "biết", "hỏi", "dùng",
        "phân", "giải", "giúp", "cần",
    }
    bad_leading = sum(
        1
        for s in sentences
        if s.split() and s.split()[0].lower() in verb_like
    )
    no_punct = sum(1 for s in sentences if not s.endswith(("?", "!")))
    return {
        "total": len(sentences),
        "with_underscore": underscore,
        "with_wh_phrase": wh_phrase,
        "bad_leading": bad_leading,
        "no_punct": no_punct,
    }


def build_report() -> str:
    from src.main import CourseAssistant
    from src.parser import Parser
    from src.grammar import CFG
    from tests.conftest import load_official_cases

    cases = load_official_cases()
    assistant = CourseAssistant()
    parser = Parser()
    grammar = CFG()

    off = evaluate_official(assistant, cases)
    par = evaluate_parser(parser, cases)
    gen = evaluate_generation(grammar)

    lines = []
    lines.append("=" * 70)
    lines.append("COURSE ASSISTANT - BASELINE METRICS")
    lines.append("=" * 70)

    lines.append("")
    lines.append(f"Official test set (tests/data/sample_queries.txt): {off['total']} cases")
    lines.append(
        f"  Intent accuracy:        {off['intent_ok']}/{off['total']} = "
        f"{off['intent_ok'] / off['total'] * 100:.2f}%"
    )
    lines.append(
        f"  Entity accuracy (alias-aware): {off['entity_ok']}/{off['total']} = "
        f"{off['entity_ok'] / off['total'] * 100:.2f}%"
    )
    lines.append(
        f"  Entity accuracy (raw match):   {off['entity_ok_strict']}/{off['total']} = "
        f"{off['entity_ok_strict'] / off['total'] * 100:.2f}%"
    )
    lines.append(
        f"  Intent + Entity accuracy: {off['combined_ok']}/{off['total']} = "
        f"{off['combined_ok'] / off['total'] * 100:.2f}%"
    )

    if off["failures"]:
        lines.append("")
        lines.append(f"  Failing cases ({len(off['failures'])}):")
        lines.extend(off["failures"])

    lines.append("")
    lines.append("Parser (on the official test set):")
    total_p = par["strict"] + par["fallback"] + par["failure"]
    lines.append(
        f"  Strict Earley chart parse: {par['strict']}/{total_p} = "
        f"{par['strict'] / total_p * 100:.2f}%"
    )
    lines.append(
        f"  Pattern fallback:        {par['fallback']}/{total_p} = "
        f"{par['fallback'] / total_p * 100:.2f}%"
    )
    lines.append(
        f"  Failure:                 {par['failure']}/{total_p} = "
        f"{par['failure'] / total_p * 100:.2f}%"
    )

    lines.append("")
    lines.append("Sentence generation:")
    lines.append(f"  Sentences generated:      {gen['total']}")
    lines.append(f"  Containing '_':            {gen['with_underscore']}")
    lines.append(f"  Containing 'WH_PHRASE':    {gen['with_wh_phrase']}")
    lines.append(f"  Bad leading token:         {gen['bad_leading']}")
    lines.append(f"  Missing end punctuation:   {gen['no_punct']}")

    lines.append("")
    lines.append("=" * 70)
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Measure Course Assistant metrics")
    parser.add_argument("--out", help="Write the report to this file as well")
    args = parser.parse_args()

    report = build_report()
    _safe_print(report)

    if args.out:
        out_path = Path(args.out)
        if not out_path.is_absolute():
            out_path = ROOT / out_path
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(report + "\n", encoding="utf-8")
        _safe_print(f"\nReport written to {out_path}")


if __name__ == "__main__":
    main()
