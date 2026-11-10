"""
Tests for the CFG grammar and the sentence generator.

The grammar is the backbone of Part I, so these tests check three things:

1. **Well-formedness** -- the grammar has no dangling symbols and every
   production refers to symbols that actually exist.
2. **Generation quality** -- generated sentences look like natural
   Vietnamese questions (no underscores, no raw non-terminals, no broken
   word order).
3. **Determinism** -- the same seed always produces the same output, which
   is what keeps ``output/samples.txt`` reproducible.
"""

import re

import pytest

from src.grammar import (
    CFG,
    COURSE_QUESTION_TEMPLATES,
    DOMAIN_CLASSES,
    generate_template_sentences,
)


@pytest.fixture(scope="module")
def cfg():
    return CFG()


@pytest.fixture(scope="module")
def generated(cfg):
    return cfg.generate_all_sentences(max_sentences=300)


# ---------------------------------------------------------------------------
# Grammar well-formedness
# ---------------------------------------------------------------------------
def test_grammar_has_a_start_symbol(cfg):
    assert cfg.start_symbol == "S"
    assert cfg.get_rules("S"), "The start symbol must have at least one production"


def test_no_dangling_nonterminals(cfg):
    """Every symbol used on a RHS must be defined or be a terminal."""
    for lhs, rules in cfg.rules.items():
        for rule in rules:
            for symbol in rule.rhs:
                assert (
                    symbol in cfg.nonterminals or cfg.is_terminal(symbol)
                ), f"{lhs} -> {rule.rhs}: undefined symbol '{symbol}'"


def test_every_nonterminal_is_productive(cfg):
    """Every non-terminal must be able to derive a terminal string."""
    productive = set(cfg.terminals)
    changed = True
    while changed:
        changed = False
        for lhs, rules in cfg.rules.items():
            if lhs in productive:
                continue
            for rule in rules:
                if all(sym in productive for sym in rule.rhs):
                    productive.add(lhs)
                    changed = True
                    break

    unreachable = cfg.nonterminals - productive
    assert not unreachable, f"Non-productive non-terminals: {sorted(unreachable)}"


def test_wh_phrase_is_defined(cfg):
    """The '?' must not be defined as a non-terminal."""
    assert "WH_PHRASE" in cfg.nonterminals
    assert "?" not in cfg.nonterminals
    assert cfg.is_terminal("?")


def test_no_duplicate_rules(cfg):
    """The same production must not appear twice under one non-terminal."""
    for lhs, rules in cfg.rules.items():
        seen = set()
        for rule in rules:
            key = tuple(rule.rhs)
            assert key not in seen, f"Duplicate rule: {lhs} -> {rule.rhs}"
            seen.add(key)


def test_all_rules_have_a_weight(cfg):
    for lhs, rules in cfg.rules.items():
        for rule in rules:
            assert rule.weight > 0, f"{rule} must have a positive weight"


def test_every_rule_has_a_comment(cfg):
    """Every production is documented -- the grammar file is self-explaining."""
    for lhs, rules in cfg.rules.items():
        for rule in rules:
            assert rule.comment, f"Missing comment for {rule}"


# ---------------------------------------------------------------------------
# Accessors
# ---------------------------------------------------------------------------
def test_terminal_classes(cfg):
    classes = cfg.get_terminal_classes()
    assert classes["cfg"] == "TOPIC_NAME"
    assert classes["nlp"] == "COURSE_NAME"
    assert classes["?"] == "PUNCT"
    # A digit is ambiguous on its own and is resolved contextually.
    assert classes["4"] == "NUM"
    assert cfg.classify_number("chương", "4") == "CHAPTER_NUM"
    assert cfg.classify_number("tuần", "3") == "WEEK_NUM"
    assert cfg.classify_number("bài", "2") == "NUM"


def test_first_sets_contain_expected_terminals(cfg):
    first = cfg.get_first_sets()
    assert "chương" in first["S"]
    assert "nlp" in first["S"]
    assert "?" in first["PUNCT"]


def test_follow_sets_are_computed(cfg):
    follow = cfg.get_follow_sets()
    assert "$" in follow["S"]
    assert "?" in follow["VP"]


def test_get_expansions(cfg):
    expansions = cfg.get_expansions("PUNCT")
    assert ["?"] in expansions


# ---------------------------------------------------------------------------
# Generation quality
# ---------------------------------------------------------------------------
def test_generation_produces_sentences(generated):
    assert len(generated) >= 200, f"Only {len(generated)} sentences generated"


def test_generated_sentences_have_no_underscores(generated):
    for sentence in generated:
        assert "_" not in sentence, f"Underscore leaked: {sentence}"


def test_generated_sentences_have_no_nonterminals(generated):
    """A non-terminal must never leak into the generated text."""
    nonterminal_pattern = re.compile(
        r"\b(" + "|".join(
            sorted(
                (n for n in CFG().nonterminals),
                key=len,
                reverse=True,
            )
        ) + r")\b"
    )
    for sentence in generated:
        match = nonterminal_pattern.search(sentence)
        assert match is None, f"Non-terminal '{match.group(0)}' leaked: {sentence}"


def test_generated_sentences_end_with_punctuation(generated):
    for sentence in generated:
        assert sentence.endswith(("?", "!")), f"Bad ending: {sentence}"


def test_generated_sentences_are_capitalized(generated):
    for sentence in generated:
        assert sentence[0].isupper(), f"Not capitalized: {sentence}"


def test_generated_sentences_have_no_double_spaces(generated):
    for sentence in generated:
        assert "  " not in sentence, f"Double space: {sentence}"


def test_generated_sentences_contain_a_domain_identifier(generated):
    """Every question must mention the course, a chapter, a week, a topic, ..."""
    domain_markers = (
        "chương", "tuần", "NLP", "CO3085", "BTL", "L.O.",
        "CFG", "PCFG", "POS", "bài tập lớn", "môn học", "ngôn ngữ tự nhiên",
        "parsing", "semantic", "syntax", "feature", "grammar",
        "tagging", "disambiguation", "assignment", "parser",
        "reference", "question answering", "selectional restriction",
        "semantic grammar", "statistical nlp", "python nlp",
    )
    for sentence in generated:
        lowered = sentence.lower()
        assert any(marker.lower() in lowered for marker in domain_markers), (
            f"No domain identifier in: {sentence}"
        )


def test_generated_sentences_do_not_repeat_the_subject(generated):
    for sentence in generated:
        for subject in ("chương", "tuần"):
            count = len(re.findall(rf"\b{subject}\b", sentence.lower()))
            assert count <= 1, f"'{subject}' repeated in: {sentence}"


def test_generated_sentences_have_no_bare_numbers(generated):
    """A number must always be introduced by 'chương' or 'tuần'."""
    words = [w.lower() for w in re.findall(r"\S+", " ".join(generated))]
    for index, word in enumerate(words):
        if word.isdigit():
            assert index > 0 and words[index - 1] in {"chương", "tuần"}, (
                f"Bare number '{word}' in the generated corpus"
            )


def test_generated_sentences_are_unique(generated):
    assert len(generated) == len(set(generated))


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------
def test_generation_is_deterministic():
    first = CFG().generate_all_sentences(max_sentences=100, seed=42)
    second = CFG().generate_all_sentences(max_sentences=100, seed=42)
    assert first == second


def test_different_seeds_give_different_corpora():
    first = CFG().generate_all_sentences(max_sentences=100, seed=42)
    second = CFG().generate_all_sentences(max_sentences=100, seed=7)
    assert first != second


# ---------------------------------------------------------------------------
# Detokenizer
# ---------------------------------------------------------------------------
def test_detokenize_unjoins_multiword_tokens(cfg):
    assert cfg.detokenize("bài_tập_lớn cần gì ?") == "Bài tập lớn cần gì?"
    assert cfg.detokenize("tín_chỉ là gì ?") == "Tín chỉ là gì?"


def test_detokenize_removes_space_before_punctuation(cfg):
    assert cfg.detokenize("chương 4 học gì ?") == "Chương 4 học gì?"


def test_detokenize_capitalizes_learning_outcomes(cfg):
    assert cfg.detokenize("l.o.2.5 là gì ?") == "L.O.2.5 là gì?"


def test_detokenize_keeps_proper_nouns(cfg):
    assert "NLP" in cfg.detokenize("nlp học gì ?")
    assert "CO3085" in cfg.detokenize("co3085 học gì ?")


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------
def test_to_string_contains_all_rules(cfg):
    text = cfg.to_string()
    for lhs in cfg.rules:
        assert f"# --- {lhs} ---" in text
    assert "S -> WH_QUESTION" in text
    assert "# " in text  # comments are present


def test_to_string_ends_with_a_newline(cfg):
    assert cfg.to_string().endswith("\n")


# ---------------------------------------------------------------------------
# Curated templates
# ---------------------------------------------------------------------------
def test_templates_expand_without_error():
    sentences = generate_template_sentences()
    assert len(sentences) > 40
    for text, intent in sentences:
        assert text.strip()
        assert intent.startswith("GET_")


def test_templates_have_no_unfilled_placeholders():
    for text, _ in generate_template_sentences():
        assert "{" not in text, f"Unfilled placeholder in: {text}"


def test_template_list_is_not_empty():
    assert len(COURSE_QUESTION_TEMPLATES) >= 30


def test_domain_classes_are_declared():
    assert "COURSE_NAME" in DOMAIN_CLASSES
    assert "TOPIC_NAME" in DOMAIN_CLASSES
