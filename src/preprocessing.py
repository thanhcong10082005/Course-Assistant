"""
Preprocessing module for Vietnamese text
Handles tokenization, normalization, and basic NLP tasks

Design notes
------------
The tokenizer works on two levels:

* ``tokenize()``       -- flat list of word tokens (kept backwards compatible)
* ``tokenize_spans()`` -- word tokens *plus* multi-word entity spans such as
  "bài tập lớn" or "tín chỉ" that would otherwise be shredded into several
  unrelated tokens.

Special identifiers of the form ``L.O.2.5`` are protected before
tokenization so that their structure survives the pipeline.
"""

import re
import unicodedata
from typing import Dict, List, Tuple

# ---------------------------------------------------------------------------
# Multi-word entities
# ---------------------------------------------------------------------------
# (normalized surface form, entity kind)
MULTIWORD_ENTITIES: List[Tuple[str, str]] = [
    ("bài_tập_lớn", "ASSIGNMENT_NAME"),
    ("tín_chỉ", "ATTRIBUTE"),
    ("giữa_kỳ", "MIDTERM"),
    ("cuối_kỳ", "FINAL"),
    ("thời_hạn", "DEADLINE"),
    ("hạn_nộp", "DEADLINE"),
    ("lịch_học", "SCHEDULE"),
    ("tài_liệu", "RESOURCE"),
    ("tham_khảo", "RESOURCE_MOD"),
    ("quy_định", "RULE"),
    ("chính_sách", "POLICY"),
    ("hỏi_đáp", "QA"),
    ("nội_dung", "CONTENT"),
    ("học_kỳ", "TERM"),
    ("môn_học", "COURSE_MOD"),
    ("đề_bài", "ASSIGNMENT_MOD"),
    ("phần_hẹn", "MEETING"),
    ("làm_quen", "ASSIGNMENT_MOD"),
]

# Pre-compiled matcher for the multi-word entities.
# The surface forms in the table use underscores, but they appear in the raw
# text with spaces -- the pattern therefore accepts both separators.
_MULTIWORD_RE = re.compile(
    "|".join(
        re.escape(surface).replace("_", r"[_\s]")
        for surface, _ in sorted(MULTIWORD_ENTITIES, key=lambda x: -len(x[0]))
    )
)

_MULTIWORD_KIND = {surface: kind for surface, kind in MULTIWORD_ENTITIES}


def _match_multiword(text: str):
    """
    Yield ``(start, end, canonical_surface, kind)`` for every multi-word
    entity found in ``text``.

    ``canonical_surface`` uses underscores (the table's canonical form) while
    ``start``/``end`` refer to the offsets inside ``text``.
    """
    for match in _MULTIWORD_RE.finditer(text):
        matched = match.group(0)
        canonical = re.sub(r"\s+", "_", matched)
        kind = _MULTIWORD_KIND.get(canonical, "ENTITY")
        yield match.start(), match.end(), canonical, kind


class Preprocessor:
    """Vietnamese text preprocessor for Course Assistant"""

    def __init__(self):
        # Stopwords that carry no intent information at all.
        self.stopwords = {
            "và", "là", "của", "trong", "với", "cho", "hay", "mà", "thì",
            "ra", "vào", "từ", "lên", "xuống", "theo", "tại", "trên", "dưới",
            "bên", "ngoài", "một", "các", "những", "có",
        }

        # Question words are *not* stopwords: they are essential for intent
        # classification ("là gì", "bao nhiêu", "ở đâu").
        self.question_words = {
            "nào", "gì", "bao", "nhiêu", "mấy", "ở", "đâu", "sao",
            "thế_nào", "như_thế_nào", "khi_nào", "bao_giờ", "ai",
        }

        # Normalization mappings for Vietnamese tone placement variants.
        self.vietnamese_mappings = {
            "òa": "oà", "óa": "oá", "ỏa": "oả", "õa": "oã",
            "ọa": "oạ", "èè": "è", "éè": "é", "ẻè": "ẻ", "ẽè": "ẽ", "ẹè": "ẹ",
        }

    # ------------------------------------------------------------------
    # Normalization
    # ------------------------------------------------------------------
    def normalize(self, text: str) -> str:
        """
        Normalize Vietnamese text:
        - Unicode NFC normalization
        - Lowercase
        - Remove extra whitespace
        """
        if not text:
            return ""

        text = unicodedata.normalize("NFC", text)
        text = text.lower()

        # Unify common tone-placement variants (oà / oà ...).
        for wrong, right in self.vietnamese_mappings.items():
            text = text.replace(wrong, right)

        text = re.sub(r"\s+", " ", text)
        text = text.strip()

        return text

    # ------------------------------------------------------------------
    # Tokenization
    # ------------------------------------------------------------------
    def tokenize(self, text: str) -> List[str]:
        """
        Simple tokenization for Vietnamese text.

        Preserves special patterns like ``L.O.X.Y`` by rewriting them to
        ``lo_X_Y`` before splitting.
        """
        if not text:
            return []

        text = self.normalize(text)

        # Protect L.O. patterns before tokenization.
        text = re.sub(r"l\.o\.(\d+)\.(\d+)", r"lo_\1_\2", text)
        text = re.sub(r"l\.o\.(\d+)", r"lo_\1", text)

        # Split by whitespace and punctuation.
        tokens = re.findall(r"\b\w+\b", text)

        return tokens

    def tokenize_spans(self, text: str) -> List[Dict]:
        """
        Tokenize *and* keep multi-word entities together.

        Returns a list of dicts::

            {
                "text":   "bài_tập_lớn",   # surface form (normalized)
                "start":  0,                # char offset in the normalized text
                "end":    12,
                "pos":    "ASSIGNMENT_NAME", # entity kind or POS tag
                "kind":   "entity",         # "entity" | "word"
            }

        Word tokens are returned with ``kind == "word"`` and the POS tag
        produced by the rule-based tagger.
        """
        if not text:
            return []

        normalized = self.normalize(text)

        # Protect L.O. patterns so that they survive as a single token.
        protected = normalized
        lo_map: Dict[str, str] = {}
        # Recover the original capitalisation (e.g. "L.O.4.2") from the raw text.
        lo_originals = {
            m.group(0).lower(): m.group(0) for m in re.finditer(r"[Ll]\.[Oo]\.\d+(?:\.\d+)?", text)
        }
        for match in re.finditer(r"l\.o\.(\d+)(?:\.(\d+))?", protected):
            original = match.group(0)
            if match.group(2):
                replacement = f"lo_{match.group(1)}_{match.group(2)}"
            else:
                replacement = f"lo_{match.group(1)}"
            lo_map[replacement] = lo_originals.get(original, original)
            protected = protected.replace(original, replacement)

        spans: List[Dict] = []

        # 1. Locate multi-word entities.
        entity_ranges = []
        for e_start, e_end, surface, kind in _match_multiword(protected):
            entity_ranges.append((e_start, e_end, surface, kind))

        # 2. Locate plain word tokens that are not covered by an entity span.
        for match in re.finditer(r"\b\w+\b", protected):
            start, end = match.span()
            if any(start >= e_start and end <= e_end for e_start, e_end, _, _ in entity_ranges):
                continue
            surface = match.group(0)
            spans.append(
                {
                    "text": surface,
                    "start": start,
                    "end": end,
                    "pos": self.get_token_pos(surface),
                    "kind": "word",
                }
            )

        # 3. Add the entity spans.
        for e_start, e_end, surface, kind in entity_ranges:
            spans.append(
                {
                    "text": surface,
                    "start": e_start,
                    "end": e_end,
                    "pos": kind,
                    "kind": "entity",
                }
            )

        spans.sort(key=lambda s: (s["start"], s["end"]))

        # 4. Restore the original L.O. surface form.
        for span in spans:
            if span["text"] in lo_map:
                span["text"] = lo_map[span["text"]]

        return spans

    # ------------------------------------------------------------------
    # Stopwords / keywords
    # ------------------------------------------------------------------
    def remove_stopwords(self, tokens: List[str], keep_question_words: bool = True) -> List[str]:
        """
        Remove Vietnamese stopwords.

        Question words are preserved by default because they are required
        for rule-based intent classification.  Pass
        ``keep_question_words=False`` to drop them as well.
        """
        removal = set(self.stopwords)
        if not keep_question_words:
            removal |= self.question_words
        return [t for t in tokens if t.lower() not in removal]

    def extract_keywords(self, text: str, keep_question_words: bool = True) -> List[str]:
        """Extract keywords from text (remove stopwords)."""
        tokens = self.tokenize(text)
        return self.remove_stopwords(tokens, keep_question_words)

    # ------------------------------------------------------------------
    # POS tagging
    # ------------------------------------------------------------------
    def get_token_pos(self, token: str) -> str:
        """Get POS tag for a single token."""
        if not token:
            return "X"

        token_lower = token.lower()

        # Multi-word entity surfaces get their dedicated kind.
        if token_lower in _MULTIWORD_KIND:
            return _MULTIWORD_KIND[token_lower]

        # Learning-outcome identifiers.
        if re.match(r"^(l\.?o\.?\d|lo_\d)", token_lower):
            return "LO_ID"

        # Course identifiers.
        if token_lower in {"nlp", "co3085", "xử_lý_ngôn_ngữ_tự_nhiên"}:
            return "COURSE_NAME"

        return VIETNAMESE_POS_TAGS.get(token_lower, "X")

    def pos_tag(self, tokens: List[str]) -> List[Tuple[str, str]]:
        """Tag a list of tokens."""
        return [(token, self.get_token_pos(token)) for token in tokens]

    # ------------------------------------------------------------------
    # Full pipeline
    # ------------------------------------------------------------------
    def preprocess(self, text: str) -> Dict:
        """
        Full preprocessing pipeline.

        Returns a dict with the original text, the normalized text, the flat
        token list, the keyword list and the richer span list.
        """
        normalized = self.normalize(text)
        tokens = self.tokenize(text)
        keywords = self.remove_stopwords(tokens)
        spans = self.tokenize_spans(text)

        return {
            "original": text,
            "normalized": normalized,
            "tokens": tokens,
            "keywords": keywords,
            "spans": spans,
        }


# ---------------------------------------------------------------------------
# Rule-based POS tagger for Vietnamese (simplified)
# ---------------------------------------------------------------------------
VIETNAMESE_POS_TAGS = {
    # --- Course / domain nouns ---
    "môn": "NOUN", "nlp": "NOUN", "co3085": "NOUN",
    "học": "VERB", "tín": "NOUN", "chỉ": "NOUN",
    "chương": "NOUN", "tuần": "NOUN", "bài": "NOUN",
    "tập": "NOUN", "lớn": "ADJ", "btl": "NOUN",
    "tài": "NOUN", "liệu": "NOUN", "quy": "NOUN",
    "định": "NOUN", "deadline": "NOUN", "hạn": "NOUN",
    "nộp": "VERB", "không": "ADV",
    "bao": "ADV", "nhiêu": "DET", "gì": "PRON",
    "nào": "DET", "ở": "PREP", "đâu": "ADV",
    "về": "PREP", "là": "VERB", "được": "AUX",
    "thông": "NOUN", "tin": "NOUN", "nói": "VERB",
    "hỏi": "VERB", "đáp": "NOUN", "yêu": "VERB",
    "cầu": "NOUN", "cần": "VERB", "muốn": "VERB",
    "biết": "VERB", "tra": "VERB", "cứu": "VERB",
    "xem": "VERB", "kiểm": "VERB", "liên": "ADJ",
    "quan": "ADJ", "tôi": "PRON", "mình": "PRON",
    "anh": "PRON", "chị": "PRON", "em": "PRON",
    "ai": "PRON", "đó": "DET", "này": "DET",
    "kia": "DET", "nọ": "DET",

    # --- Multi-word components ---
    "giữa": "NOUN", "kỳ": "NOUN", "cuối": "NOUN",
    "tham": "NOUN", "khảo": "NOUN", "chính": "NOUN",
    "sách": "NOUN", "phần": "NOUN", "nội": "NOUN",
    "dung": "NOUN", "lịch": "NOUN", "học_kỳ": "NOUN",
    "môn_học": "NOUN", "giữa_kỳ": "NOUN", "cuối_kỳ": "NOUN",

    # --- Verbs ---
    "có": "VERB", "triển": "VERB", "khai": "VERB",
    "báo": "VERB", "dùng": "VERB", "phép": "ADJ",
    "phân": "VERB", "giải": "VERB", "giúp": "VERB",
    "học_về": "VERB", "nói_về": "VERB", "trình_bày": "VERB",

    # --- Adpositions / adverbs ---
    "sau": "ADP", "trước": "ADP", "kế": "ADP",
    "tiếp": "ADP", "còn": "ADP", "nữa": "ADV",
    "thế_nào": "ADV", "như_thế_nào": "ADV",
    "hôm": "NOUN", "nay": "PRON", "bây": "ADV",
    "giờ": "NOUN", "chính": "ADV", "sao": "PRON",

    # --- Numbers ---
    "1": "NUM", "2": "NUM", "3": "NUM", "4": "NUM",
    "5": "NUM", "6": "NUM", "7": "NUM", "8": "NUM",
    "9": "NUM", "10": "NUM", "11": "NUM", "12": "NUM",
    "13": "NUM", "14": "NUM", "15": "NUM", "16": "NUM",
    "30": "NUM", "60": "NUM", "90": "NUM", "99": "NUM",

    # --- Topics ---
    "cfg": "NOUN", "pcfg": "NOUN", "pos": "NOUN",
    "parsing": "NOUN", "semantic": "NOUN", "syntax": "NOUN",
    "grammar": "NOUN", "feature": "NOUN", "anaphora": "NOUN",
    "centering": "NOUN", "reference": "NOUN", "wsd": "NOUN",
    "tagging": "NOUN", "disambiguation": "NOUN",

    # --- Assignment parts ---
    "part": "NOUN", "i": "NUM", "ii": "NUM", "iii": "NUM", "iv": "NUM",
}


def pos_tag(tokens: List[str]) -> List[Tuple[str, str]]:
    """Simple rule-based POS tagging for the Course Assistant domain."""
    tagger = Preprocessor()
    return tagger.pos_tag(tokens)


def get_token_pos(token: str) -> str:
    """Get POS tag for a single token."""
    return Preprocessor().get_token_pos(token)
