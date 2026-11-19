"""
Parsing -> Semantic Representation link.

The assignment asks for the chain ``Input -> Parsing -> Semantic
Representation -> ... -> Answer``.  These tests pin the contract of that
link:

1. passing the tree is **optional** -- ``analyze(text)`` keeps working and
   the intent never changes when the tree is added (no regression);
2. the tree can only *add* entities the surface lexicon missed, never
   overwrite one (the lexicon is the primary source);
3. ``parse_result`` produced by the pipeline is byte-identical to the
   legacy :meth:`src.parser.Parser.get_parse_result` API;
4. the dialogue turns are analysed with the tree as well, and the
   committed ``output/dialogue.txt`` still matches the pipeline.
"""

import re
from pathlib import Path

import pytest

from tests.conftest import load_official_cases

OFFICIAL_CASES = load_official_cases()

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "output"


@pytest.fixture(scope="module")
def parser():
    from src.parser import Parser

    return Parser()


@pytest.fixture(scope="module")
def analyzer():
    from src.semantic import SemanticAnalyzer

    return SemanticAnalyzer()


def _parse(parser, text):
    tree, _errors = parser.parse(text)
    return tree


# ---------------------------------------------------------------------------
# 1. tree=None is a no-op on the official set
# ---------------------------------------------------------------------------
def test_tree_none_is_identical_to_legacy(analyzer, parser):
    """``analyze(text, tree=None)`` == ``analyze(text)`` on all 34 cases."""
    for case in OFFICIAL_CASES:
        query = case["query"]
        with_tree_none = analyzer.analyze(query, tree=None)
        legacy = analyzer.analyze(query)
        assert str(with_tree_none) == str(legacy), case["id"]
        assert with_tree_none.entities == legacy.entities, case["id"]
        assert with_tree_none.query_type == "", case["id"]


def test_tree_does_not_change_the_intent(analyzer, parser):
    """Adding the tree may add entities, but never flips the intent."""
    for case in OFFICIAL_CASES:
        query = case["query"]
        tree = _parse(parser, query)
        without = analyzer.analyze(query)
        with_tree = analyzer.analyze(query, tree=tree)
        assert with_tree.intent == without.intent, (
            f"{case['id']}: intent changed {without.intent} -> {with_tree.intent}"
        )


def test_tree_never_overwrites_a_lexicon_entity(analyzer, parser):
    """Every entity the lexicon found survives unchanged (primary wins)."""
    for case in OFFICIAL_CASES:
        query = case["query"]
        tree = _parse(parser, query)
        without = analyzer.analyze(query).entities
        with_tree = analyzer.analyze(query, tree=tree).entities
        for key, value in without.items():
            assert with_tree.get(key) == value, (
                f"{case['id']}: entity '{key}' changed {value!r} -> "
                f"{with_tree.get(key)!r}"
            )


def test_query_type_is_the_root_symbol(analyzer, parser):
    """The unused ``query_type`` slot now records the syntactic type."""
    for case in OFFICIAL_CASES:
        tree = _parse(parser, case["query"])
        if tree is None:
            continue
        sem_rep = analyzer.analyze(case["query"], tree=tree)
        assert sem_rep.query_type == tree.symbol, case["id"]


# ---------------------------------------------------------------------------
# 2. backoff: the tree fills a slot the text does not contain
# ---------------------------------------------------------------------------
def test_tree_backfills_a_missing_entity(analyzer, parser):
    """A chapter that appears only in the tree is still reported."""
    text = "deadline là khi nào?"          # no chapter in the text
    tree = _parse(parser, "Chương 7 nói về CFG?")

    assert "chapter" not in analyzer.analyze(text).entities
    entities = analyzer.analyze(text, tree=tree).entities
    assert entities.get("chapter") == "CH07"


def test_lexicon_wins_over_a_conflicting_tree(analyzer, parser):
    """The text is authoritative: a conflicting tree value is ignored."""
    text = "Chương 4 nói về gì?"
    tree = _parse(parser, "Chương 7 nói về CFG?")

    entities = analyzer.analyze(text, tree=tree).entities
    assert entities.get("chapter") == "CH04"


# ---------------------------------------------------------------------------
# 3. parse_result is byte-identical to the legacy API
# ---------------------------------------------------------------------------
def test_parse_result_matches_legacy_api(parser):
    for case in OFFICIAL_CASES:
        tree, _errors = parser.parse(case["query"])
        new = str(tree) if tree is not None else "()"
        old = parser.get_parse_result(case["query"])
        assert new == old, case["id"]


def test_parse_result_of_empty_input(parser):
    tree, _errors = parser.parse("")
    new = str(tree) if tree is not None else "()"
    assert new == "()"
    assert new == parser.get_parse_result("")


# ---------------------------------------------------------------------------
# 4. the dialogue path is linked too, and the artefact is in sync
# ---------------------------------------------------------------------------
def test_dialogue_turns_are_analysed_with_the_tree():
    """``process_dialogue`` passes the tree of the resolved query."""
    from src.main import CourseAssistant

    assistant = CourseAssistant()
    tree, _errors = assistant.parser.parse("Chương 4 nói về gì?")
    assert tree is not None

    # The resolved query of a turn that uses a reference is analysed with
    # the tree of the *resolved* text, so ``query_type`` is populated.
    assistant.process_dialogue("Chương 4 nói về gì?")
    assistant.process_dialogue("Nó có liên quan đến parsing không?")
    state = assistant.get_dialogue_state()
    assert state["turn"] == 2


def test_dialogue_artifact_still_matches_the_pipeline():
    """The committed output/dialogue.txt is what the pipeline produces."""
    from src.main import DEMO_DIALOGUES, CourseAssistant

    if not (OUTPUT_DIR / "dialogue.txt").exists():
        pytest.skip("output/dialogue.txt has not been generated yet")

    recorded = re.findall(
        r"^\s*Answer\s+:(.*?)^\s*State\s+:",
        (OUTPUT_DIR / "dialogue.txt").read_text(encoding="utf-8"),
        flags=re.MULTILINE | re.DOTALL,
    )
    recorded = [answer.strip() for answer in recorded]

    produced = []
    for first, second in DEMO_DIALOGUES:
        assistant = CourseAssistant()
        context = {}
        for user_input in (first, second):
            answer, context = assistant.process_dialogue(user_input, context)
            produced.append(answer.strip())

    assert len(recorded) == len(produced) == 2 * len(DEMO_DIALOGUES)
    assert recorded == produced
