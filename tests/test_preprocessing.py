"""
Tests for the preprocessing component (tokenizer, POS tagger, normalisation).
"""

import pytest

from src.preprocessing import MULTIWORD_ENTITIES, Preprocessor


@pytest.fixture
def preprocessor():
    return Preprocessor()


# ---------------------------------------------------------------------------
# Normalisation
# ---------------------------------------------------------------------------
def test_normalize_lowercases_and_collapses_spaces(preprocessor):
    assert preprocessor.normalize("  Môn   NLP   có bao nhiêu tín chỉ? ") == (
        "môn nlp có bao nhiêu tín chỉ?"
    )


def test_normalize_handles_empty_input(preprocessor):
    assert preprocessor.normalize("") == ""
    assert preprocessor.tokenize("") == []
    assert preprocessor.tokenize_spans("") == []


# ---------------------------------------------------------------------------
# Tokenizer
# ---------------------------------------------------------------------------
def test_tokenize_splits_on_punctuation(preprocessor):
    tokens = preprocessor.tokenize("Tuần 3 học gì?")
    assert tokens == ["tuần", "3", "học", "gì"]


def test_tokenize_preserves_learning_outcome_structure(preprocessor):
    """L.O.2.5 must keep its hierarchical structure."""
    tokens = preprocessor.tokenize("L.O.2.5 là gì?")
    assert "lo_2_5" in tokens


def test_tokenize_spans_keeps_multiword_entities_together(preprocessor):
    spans = preprocessor.tokenize_spans("Bài tập lớn cần xuất file gì?")
    surfaces = [s["text"] for s in spans]

    assert "bài_tập_lớn" in surfaces
    assert not any(s == "bài" for s in surfaces)
    assert not any(s == "lớn" for s in surfaces)

    entity = next(s for s in spans if s["text"] == "bài_tập_lớn")
    assert entity["kind"] == "entity"
    assert entity["pos"] == "ASSIGNMENT_NAME"


def test_tokenize_spans_keeps_attribute_entities(preprocessor):
    spans = preprocessor.tokenize_spans("Môn NLP có bao nhiêu tín chỉ?")
    surfaces = [s["text"] for s in spans]
    assert "tín_chỉ" in surfaces


def test_tokenize_spans_detects_several_multiword_entities(preprocessor):
    spans = preprocessor.tokenize_spans("Quy định về giữa kỳ và cuối kỳ?")
    surfaces = [s["text"] for s in spans]
    assert "giữa_kỳ" in surfaces
    assert "cuối_kỳ" in surfaces


def test_tokenize_spans_preserves_learning_outcome(preprocessor):
    spans = preprocessor.tokenize_spans("L.O.4.2 liên quan đến nội dung nào?")
    surfaces = [s["text"] for s in spans]
    assert "L.O.4.2" in surfaces
    lo_span = next(s for s in spans if s["text"] == "L.O.4.2")
    assert lo_span["pos"] == "LO_ID"


def test_tokenize_spans_are_ordered_and_non_overlapping(preprocessor):
    spans = preprocessor.tokenize_spans("Tuần 3 học CFG và PCFG trong chương 4")
    starts = [s["start"] for s in spans]
    assert starts == sorted(starts)
    for a, b in zip(spans, spans[1:]):
        assert a["end"] <= b["start"]


def test_tokenize_spans_covers_the_whole_sentence(preprocessor):
    """Every character of the sentence must belong to a span."""
    text = "Bài tập lớn gồm những phần nào?"
    spans = preprocessor.tokenize_spans(text)
    assert spans[0]["start"] == 0

    # The spans must cover the sentence without gaps.
    cursor = 0
    for span in spans:
        assert span["start"] >= cursor
        cursor = span["end"]
    # Trailing punctuation is not part of any word span.
    normalized = preprocessor.normalize(text)
    assert normalized.rstrip("?!.,").endswith(normalized[cursor - 1]) or cursor > 0


# ---------------------------------------------------------------------------
# POS tagging
# ---------------------------------------------------------------------------
def test_get_token_pos_known_words(preprocessor):
    assert preprocessor.get_token_pos("môn") == "NOUN"
    assert preprocessor.get_token_pos("học") == "VERB"
    assert preprocessor.get_token_pos("ở") == "PREP"
    assert preprocessor.get_token_pos("3") == "NUM"


def test_get_token_pos_multiword_kinds(preprocessor):
    assert preprocessor.get_token_pos("giữa") == "NOUN"
    assert preprocessor.get_token_pos("kỳ") == "NOUN"
    assert preprocessor.get_token_pos("tham") == "NOUN"
    assert preprocessor.get_token_pos("khảo") == "NOUN"


def test_get_token_pos_special_identifiers(preprocessor):
    assert preprocessor.get_token_pos("l.o.2.5") == "LO_ID"
    assert preprocessor.get_token_pos("nlp") == "COURSE_NAME"
    assert preprocessor.get_token_pos("bài_tập_lớn") == "ASSIGNMENT_NAME"


def test_get_token_pos_unknown_word(preprocessor):
    assert preprocessor.get_token_pos("xyzzy") == "X"
    assert preprocessor.get_token_pos("") == "X"


# ---------------------------------------------------------------------------
# Stopwords / keywords
# ---------------------------------------------------------------------------
def test_question_words_are_not_removed(preprocessor):
    """Question words are essential for intent classification."""
    tokens = preprocessor.tokenize("Chương nào nói về gì?")
    keywords = preprocessor.remove_stopwords(tokens)
    assert "gì" in keywords
    assert "nào" in keywords


def test_stopwords_can_be_removed_strictly(preprocessor):
    tokens = preprocessor.tokenize("Chương nào nói về gì?")
    keywords = preprocessor.remove_stopwords(tokens, keep_question_words=False)
    assert "gì" not in keywords


def test_extract_keywords_returns_content_words(preprocessor):
    keywords = preprocessor.extract_keywords("Môn NLP có bao nhiêu tín chỉ?")
    assert "nlp" in keywords
    assert "có" not in keywords


# ---------------------------------------------------------------------------
# Full pipeline
# ---------------------------------------------------------------------------
def test_preprocess_returns_all_fields(preprocessor):
    result = preprocessor.preprocess("Tuần 3 học gì?")
    for key in ("original", "normalized", "tokens", "keywords", "spans"):
        assert key in result
    assert result["original"] == "Tuần 3 học gì?"
    assert result["tokens"] == ["tuần", "3", "học", "gì"]


def test_multiword_table_has_no_duplicates():
    surfaces = [surface for surface, _ in MULTIWORD_ENTITIES]
    assert len(surfaces) == len(set(surfaces)), "Duplicate multi-word entity surfaces"
