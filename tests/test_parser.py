"""
Tests for the Earley chart parser.

The parser used to be a hand-written recursive-descent parser that only
handled 4/34 of the official questions *strictly*.  It is now an
**Earley chart parser** driven by the productions of :mod:`src.grammar`, so
these tests check

1. that the strict parser accepts the official questions,
2. that the parse tree is **complete** -- every token of the input appears
   exactly once in the tree (this is the guard against the span-mixing bug
   that silently dropped tokens such as the "4" of "Chương 4"), and
3. that the legacy API (``parse``, ``tokenize_input``, ``get_parse_result``,
   ``parse_strict``) still behaves as before.
"""

import pytest

from src.grammar import CFG
from src.parser import Parser

from tests.conftest import load_official_cases


@pytest.fixture(scope="module")
def parser():
    return Parser(CFG())


OFFICIAL_CASES = load_official_cases()


# ---------------------------------------------------------------------------
# Strict parsing on the official test set
# ---------------------------------------------------------------------------
def test_strict_parse_covers_most_official_queries(parser):
    """At least 90 % of the official questions must parse strictly."""
    strict = 0
    for case in OFFICIAL_CASES:
        if parser.parse_strict(case["query"]) is not None:
            strict += 1
    ratio = strict / len(OFFICIAL_CASES)
    assert ratio >= 0.90, f"Only {strict}/{len(OFFICIAL_CASES)} strict parses"


def test_parse_always_produces_a_tree(parser):
    """The fallback guarantees a tree for every official question."""
    for case in OFFICIAL_CASES:
        tree, errors = parser.parse(case["query"])
        assert tree is not None, f"{case['id']} produced no tree"


def test_parse_reports_no_error_when_a_tree_was_built(parser):
    for case in OFFICIAL_CASES:
        tree, errors = parser.parse(case["query"])
        if tree is not None:
            assert errors == []


# ---------------------------------------------------------------------------
# Tree completeness -- the important regression guard
# ---------------------------------------------------------------------------
COMPLETENESS_CASES = [
    "Chương 4 nói về gì?",
    "Tuần 3 học gì?",
    "Môn NLP có bao nhiêu tín chỉ?",
    "Chương 11 có hỏi đáp không?",
    "Chương nào nói về semantic grammar?",
    "Tài liệu về PCFG ở đâu?",
    "L.O.4.2 là gì?",
]


@pytest.mark.parametrize("sentence", COMPLETENESS_CASES)
def test_parse_tree_contains_every_token(parser, sentence):
    """
    Every word of the input must appear in the tree -- in order and exactly
    once.  The span table used to be keyed by ``(rule, dot)``
    without the token position, so the tree builder could pick a span that
    did not start where the derivation stood and tokens were dropped
    ("Chương 4" produced a tree containing only "chương").
    """
    tree, _errors = parser.parse(sentence)
    assert tree is not None, f"No tree for: {sentence}"

    def norm(text):
        """Keep only the letters and digits, lower-cased."""
        return "".join(
            ch for ch in text.lower() if ch.isalnum()
        )

    leaves = norm("".join(tree.leaves()))
    expected = norm(sentence)

    assert leaves == expected, (
        f"Tree does not cover the input for: {sentence}\n"
        f"  leaves   : {leaves}\n"
        f"  expected : {expected}"
    )


def test_parse_tree_root_is_a_question_type(parser):
    tree, _errors = parser.parse("Chương 4 nói về gì?")
    assert tree.symbol in {"WH_QUESTION", "YES_NO_QUESTION"}


def test_parse_tree_has_a_reasonable_depth(parser):
    tree, _errors = parser.parse("Chương 4 nói về gì?")
    assert tree.height() >= 3


# ---------------------------------------------------------------------------
# Tokenization
# ---------------------------------------------------------------------------
def test_tokenize_keeps_multiword_entities_together(parser):
    tokens = parser.tokenize_input("Bài tập lớn cần xuất file gì?")
    surfaces = [surface for surface, _pos in tokens]
    assert any("bài_tập_lớn" in surface for surface in surfaces)


def test_tokenize_emits_the_question_mark_as_a_token(parser):
    tokens = parser.tokenize_input("Chương 4 nói về gì?")
    assert ("?", "PUNCT") in tokens


def test_tokenize_protects_learning_outcome_ids(parser):
    tokens = parser.tokenize_input("L.O.2.5 là gì?")
    surfaces = [surface for surface, _pos in tokens]
    assert any(surface.lower().replace(".", "_") == "l_o_2_5" for surface in surfaces)
    assert any(pos == "LO_ID" for _surface, pos in tokens)


# ---------------------------------------------------------------------------
# Legacy API
# ---------------------------------------------------------------------------
def test_get_parse_result_returns_a_printable_tree(parser):
    result = parser.get_parse_result("Chương 4 nói về gì?")
    assert result.startswith("(")
    assert result.endswith(")")


def test_get_parse_result_of_an_empty_input(parser):
    assert parser.get_parse_result("") == "()"


def test_parse_strict_returns_none_for_a_non_question(parser):
    """A fragment that is not a question is outside the grammar."""
    assert parser.parse_strict("xyz abc") is None
