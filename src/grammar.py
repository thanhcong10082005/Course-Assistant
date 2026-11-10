"""
CFG Grammar for the Course Assistant domain.

The grammar is the single source of truth for the Part I deliverables:

* it *generates* the sample sentences (``output/samples.txt``), and
* it *drives* the parser (``src/parser.py``) -- the parser reads its
  productions, terminal classes and FIRST/FOLLOW sets from here instead of
  hard-coding a second, divergent copy of the language.

Design notes
------------
* Every production carries a **weight**.  The generator samples proportional
  to the weight, which is what makes the generated Vietnamese sound natural
  ("Chương 4 nói về gì?" is far more likely than "Tra với chương 4").
* Every production carries an optional **comment** that is written to
  ``output/grammar.txt`` so the grammar file is self-documenting.
* Subject nouns ("chương", "tuần") live inside the noun phrase, while the
  question words ("gì", "nào", "bao nhiêu", "ở đâu") live inside the verb
  phrase.  This mirrors how Vietnamese questions are actually built and
  prevents artefacts such as "tuần tuần 15".
* The generator applies **constraints** (forbidden adjacencies, forbidden
  first tokens, mandatory domain identifier) and finally **detokenises** the
  result so that ``bài_tập_lớn`` becomes ``bài tập lớn``.

Vocabulary extension
--------------------
The vocabulary was extended so that the grammar also covers the *natural*
Vietnamese question patterns of the official test set:

* multi-word domain entities (``tín chỉ``, ``bài tập lớn``, ``quy định``,
  ``sử dụng``, ``phương pháp``, ``semantic grammar``, ...),
* the modal / auxiliary verbs (``được``, ``phải``, ``cần``, ``muốn``),
* quantifiers (``bao nhiêu``, ``mấy``),
* post-modifiers (``quy định về sử dụng AI``) and
* elliptical questions (``Còn chương sau?``).
"""

import random
import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

# ---------------------------------------------------------------------------
# Terminal glue: how underscore-joined terminals are written in running text
# ---------------------------------------------------------------------------
TOKEN_GLUE: Dict[str, str] = {
    "bài_tập_lớn": "bài tập lớn",
    "tín_chỉ": "tín chỉ",
    "môn_học": "môn học",
    "học_phần": "học phần",
    "giữa_kỳ": "giữa kỳ",
    "cuối_kỳ": "cuối kỳ",
    "học_kỳ": "học kỳ",
    "lịch_học": "lịch học",
    "hạn_nộp": "hạn nộp",
    "tài_liệu": "tài liệu",
    "tham_khảo": "tham khảo",
    "quy_định": "quy định",
    "chính_sách": "chính sách",
    "hỏi_đáp": "hỏi đáp",
    "nội_dung": "nội dung",
    "thời_hạn": "thời hạn",
    "đề_bài": "đề bài",
    "làm_quen": "làm quen",
    "xử_lý_ngôn_ngữ_tự_nhiên": "xử lý ngôn ngữ tự nhiên",
    "sử_dụng": "sử dụng",
    "xây_dựng": "xây dựng",
    "phương_pháp": "phương pháp",
    "đồ_án": "đồ án",
    "bài_giảng": "bài giảng",
    "ghi_chú": "ghi chú",
    "kiểm_tra": "kiểm tra",
    "tiêu_chí": "tiêu chí",
    "thành_viên": "thành viên",
    "quan_trọng": "quan trọng",
    "liên_quan": "liên quan",
    "nói_về": "nói về",
    "học_về": "học về",
    "bao_gồm": "bao gồm",
    "trình_bày": "trình bày",
    "báo_cáo": "báo cáo",
    "kéo_dài": "kéo dài",
    "giới_thiệu": "giới thiệu",
    "định_nghĩa": "định nghĩa",
    "thế_nào": "thế nào",
    "kế_tiếp": "kế tiếp",
    "bao_nhiêu": "bao nhiêu",
    "khi_nào": "khi nào",
    "ở_đâu": "ở đâu",
    "bao_giờ": "bao giờ",
    "semantic_grammar": "semantic grammar",
    "statistical_nlp": "statistical nlp",
    "python_nlp": "python nlp",
    "question_answering": "question answering",
    "selectional_restriction": "selectional restriction",
    "top_down": "top-down",
    "bottom_up": "bottom-up",
    "best_first": "best-first",
    "llm_rag": "LLM/RAG",
    "tp.hcm": "TP.HCM",
    "tp_hcm": "TP.HCM",
    "thời_hạn": "thời hạn",
    "hạn_nộp": "hạn nộp",
    "lịch_học": "lịch học",
    "bài_giảng": "bài giảng",
    "ghi_chú": "ghi chú",
    "kiểm_tra": "kiểm tra",
    "tiêu_chí": "tiêu chí",
    "thành_viên": "thành viên",
    "quan_trọng": "quan trọng",
    "phần_hẹn": "phần hẹn",
    "làm_quen": "làm quen",
    "đề_bài": "đề bài",
    "học_kỳ": "học kỳ",
    "xử_lý_ngôn_ngữ_tự_nhiên": "xử lý ngôn ngữ tự nhiên",
    "thư_viện": "thư viện",
    "đồ_án": "đồ án",
    "thông_tin": "thông tin",
    "yêu_cầu": "yêu cầu",
    "phần_này": "phần này",
    "l.o.1.1": "L.O.1.1",
}

# Terminals that must keep a canonical capitalisation in the output.
CAPITALISED_TERMINALS: Dict[str, str] = {
    "nlp": "NLP",
    "co3085": "CO3085",
    "pcfg": "PCFG",
    "cfg": "CFG",
    "pos": "POS",
    "btl": "BTL",
    "atn": "ATN",
    "tp.hcm": "TP.HCM",
    "tp_hcm": "TP.HCM",
    "statistical nlp": "Statistical NLP",
    "python nlp": "Python NLP",
    "semantic grammar": "Semantic Grammar",
    "l.o.1.1": "L.O.1.1",
}

# Terminals that must not open a generated sentence.
NOT_FIRST: Set[str] = {
    "tra", "xem", "tìm", "muốn", "biết", "hỏi", "dùng", "phân",
    "giải", "giúp", "cần", "deadline", "l.o.1.1", "dùng", "xây_dựng",
    "báo_cáo", "nằm", "kéo_dài", "giới_thiệu", "định_nghĩa",
    # Weak quantifiers make the question read oddly in first position.
    "mấy", "bao", "nhiêu", "những", "các",
}

# Token pairs that must never be adjacent (grammatically broken combinations).
FORBIDDEN_ADJACENT: List[Set[str]] = [
    {"DET", "DET"},
    {"ADJ", "ADJ"},
    {"WH_QWORD", "WH_QWORD"},
    {"NUM", "NUM"},
]

# Terminals that denote a domain entity of the course.  A question that
# contains none of them is not a meaningful course question.
DOMAIN_TERMINALS: Set[str] = {
    # courses
    "nlp", "co3085", "xử_lý_ngôn_ngữ_tự_nhiên",
    # chapters & weeks
    "chương", "tuần",
    # topics
    "cfg", "pcfg", "parsing", "semantic", "syntax", "pos",
    "feature", "grammar", "tagging", "disambiguation", "parser",
    # assignments & learning outcomes
    "btl", "bài_tập_lớn", "assignment",
}

# Learning-outcome identifiers are generated in a fixed pattern.
LO_TERMINAL_RE = re.compile(r"^l\.o\.\d+(?:\.\d+)?$")

# Grammar classes that make a sentence meaningful as a course question.
DOMAIN_CLASSES: Set[str] = {
    "COURSE_NAME", "CHAPTER_REF", "WEEK_REF", "TOPIC_NAME",
    "ASSIGNMENT_NAME", "LO_ID",
}

# Non-terminals whose expansions denote a domain entity of the course.
DOMAIN_NONTERMINALS: Set[str] = {
    "COURSE_NAME", "CHAPTER_REF", "WEEK_REF", "TOPIC_NAME",
    "ASSIGNMENT_NAME", "LO_ID",
}

# Classes whose terminals are ambiguous on their own (a digit can be a
# chapter number or a week number) and are therefore resolved contextually.
AMBIGUOUS_CLASSES: Set[str] = {"CHAPTER_NUM", "WEEK_NUM"}


@dataclass
class GrammarRule:
    """A single CFG production rule."""

    lhs: str
    rhs: List[str]
    weight: float = 1.0
    comment: str = ""

    def __repr__(self) -> str:
        return f"{self.lhs} -> {' '.join(self.rhs)}"

    def __str__(self) -> str:
        return self.__repr__()

    def to_line(self) -> str:
        """Render the rule for ``output/grammar.txt`` (with comment)."""
        line = f"{self.lhs} -> {' '.join(self.rhs)}"
        if self.comment:
            line += f"    # {self.comment}"
        return line


class CFG:
    """Context-free grammar for Course Assistant questions."""

    def __init__(self, seed: int = 42):
        self.rules: Dict[str, List[GrammarRule]] = {}
        self.terminals: Set[str] = set()
        self.nonterminals: Set[str] = set()
        self.start_symbol = "S"
        self.rng = random.Random(seed)
        self._terminal_classes: Optional[Dict[str, str]] = None
        self._first_sets: Optional[Dict[str, Set[str]]] = None
        self._follow_sets: Optional[Dict[str, Set[str]]] = None
        self._build_grammar()

    # ------------------------------------------------------------------
    # Rule registration
    # ------------------------------------------------------------------
    def _add_rule(self, lhs: str, rhs: List[str], weight: float = 1.0, comment: str = "") -> None:
        """Register a production rule."""
        rule = GrammarRule(lhs, rhs, weight, comment)
        self.rules.setdefault(lhs, []).append(rule)
        self.nonterminals.add(lhs)
        for symbol in rhs:
            if self._looks_terminal(symbol):
                self.terminals.add(symbol)
            else:
                self.nonterminals.add(symbol)

    @staticmethod
    def _looks_terminal(symbol: str) -> bool:
        """Terminals are lower-case words, digits or punctuation."""
        if symbol in {"?", "!"}:
            return True
        if symbol.isdigit():
            return True
        return symbol.islower()

    # ------------------------------------------------------------------
    # Grammar definition
    # ------------------------------------------------------------------
    def _build_grammar(self) -> None:
        """Build the grammar for the Course Assistant domain."""

        # -- Sentence / question types ---------------------------------
        self._add_rule("S", ["WH_QUESTION"], weight=3.0, comment="câu hỏi từ hạ từ")
        self._add_rule("S", ["YES_NO_QUESTION"], weight=1.0, comment="câu hỏi có/không")

        # Alias kept for documentation purposes; WH_PHRASE is a real
        # non-terminal so that the grammar contains no dangling symbol.
        self._add_rule("QUESTION", ["WH_QUESTION"], comment="alias tổng quát")
        self._add_rule("WH_PHRASE", ["WH_QWORD"], comment="cụm từ hỏi")

        self._add_rule(
            "WH_QUESTION",
            ["WH_QWORD", "NP", "VP", "PUNCT"],
            weight=2.0,
            comment="từ hỏi + NP + VP + ?",
        )
        self._add_rule(
            "WH_QUESTION",
            ["WH_QWORD", "NP", "MODS", "VP", "PUNCT"],
            weight=1.0,
            comment="từ hỏi + NP + PP + VP + ?",
        )
        self._add_rule(
            "WH_QUESTION",
            ["NP", "VP", "PUNCT"],
            weight=4.0,
            comment="NP + VP + ? (từ hỏi nằm trong VP)",
        )
        self._add_rule(
            "WH_QUESTION",
            ["NP", "MODS", "VP", "PUNCT"],
            weight=2.0,
            comment="NP + PP + VP + ?",
        )
        self._add_rule(
            "WH_QUESTION",
            ["VP", "PUNCT"],
            weight=1.5,
            comment="VP + ? (câu hỏi không có chủ ngữ rõ ràng)",
        )
        self._add_rule(
            "WH_QUESTION",
            ["NP", "PUNCT"],
            weight=1.0,
            comment="NP + ? (câu hỏi rút gọn)",
        )
        self._add_rule(
            "WH_QUESTION",
            ["WH_QWORD", "NP", "PUNCT"],
            weight=1.0,
            comment="từ hỏi + NP + ?",
        )
        self._add_rule(
            "YES_NO_QUESTION",
            ["NP", "VP", "PUNCT"],
            weight=2.5,
            comment="NP + VP + ?",
        )
        self._add_rule(
            "YES_NO_QUESTION",
            ["NP", "MODS", "VP", "PUNCT"],
            weight=1.5,
            comment="NP + PP + VP + ?",
        )
        self._add_rule(
            "YES_NO_QUESTION",
            ["VP", "PUNCT"],
            weight=2.0,
            comment="VP + ?",
        )
        self._add_rule(
            "YES_NO_QUESTION",
            ["ADV", "NP", "PUNCT"],
            weight=1.0,
            comment="ADV + NP + ? (câu hỏi rút gọn 'Còn ...?')",
        )
        self._add_rule(
            "YES_NO_QUESTION",
            ["ADV", "NP", "VP", "PUNCT"],
            weight=1.0,
            comment="ADV + NP + VP + ?",
        )
        self._add_rule(
            "YES_NO_QUESTION",
            ["NP", "PUNCT"],
            weight=1.0,
            comment="NP + ?",
        )

        # -- Question words (live inside the verb phrase) ---------------
        for word, weight, comment in [
            ("gì", 4.0, "từ hỏi nội dung"),
            ("nào", 3.0, "từ hỏi chọn lựa"),
            ("bao_nhiêu", 2.0, "lượng từ"),
            ("ở_đâu", 2.0, "địa điểm"),
            ("khi_nào", 1.5, "thời điểm"),
            ("thế_nào", 1.0, "cách thức"),
            ("ai", 1.0, "chủ thể người"),
            ("bao_giờ", 0.8, "thời điểm (viết tắt)"),
        ]:
            self._add_rule("WH_QWORD", [word], weight=weight, comment=comment)

        # -- Noun phrases ----------------------------------------------
        for rhs, weight, comment in [
            (["COURSE_REF"], 2.5, "tên môn học kèm chỉ danh"),
            (["CHAPTER_REF"], 3.0, "chương + (số | nào)"),
            (["WEEK_REF"], 3.0, "tuần + (số | nào)"),
            (["TOPIC_NAME"], 2.5, "chủ đề"),
            (["ASSIGNMENT_NAME"], 2.0, "tên bài tập lớn"),
            (["TECH_NAME"], 1.2, "công nghệ (LLM/RAG, AI)"),
            (["LO_ID"], 1.5, "mã mục tiêu học tập"),
            (["ATTR_NOUN"], 1.5, "thuộc tính (tín chỉ, phút, midterm...)"),
            (["PART_REF"], 1.0, "phần của bài tập lớn"),
            (["DET", "NOMINAL"], 2.5, "danh từ có từ chỉ định"),
            (["DET", "WH_QWORD"], 1.0, "từ chỉ định + từ hỏi"),
            (["NOMINAL"], 3.0, "danh từ đơn"),
            (["NOMINAL", "NOMINAL"], 1.2, "danh từ ghép ('tài liệu tham khảo')"),
            (["NOMINAL", "WH_QWORD"], 0.8, "danh từ + từ hỏi ('sử dụng ai')"),
            (["PRONOUN"], 0.5, "đại từ"),
            (["WH_QWORD"], 1.0, "từ hỏi đóng vai trò danh từ"),
            (["QUANT", "ATTR_NOUN"], 1.0, "lượng từ + thuộc tính"),
            (["NOMINAL", "PP"], 1.5, "danh từ + PP (hậu tố)"),
            (["COURSE_REF", "PP"], 0.8, "tên môn + PP (hậu tố)"),
        ]:
            self._add_rule("NP", rhs, weight=weight, comment=comment)

        # -- Course references -----------------------------------------
        self._add_rule("COURSE_REF", ["COURSE_NAME"], weight=2.0, comment="tên môn")
        self._add_rule(
            "COURSE_REF", ["COURSE_MOD", "COURSE_NAME"], weight=3.0, comment="'môn' + tên môn"
        )
        self._add_rule("COURSE_REF", ["COURSE_MOD"], weight=1.0, comment="'môn học'")

        for name in ("nlp", "co3085", "xử_lý_ngôn_ngữ_tự_nhiên"):
            self._add_rule("COURSE_NAME", [name], comment="mã / tên môn")

        for name in ("môn", "môn_học", "học_phần"):
            self._add_rule("COURSE_MOD", [name], comment="chỉ danh môn học")

        # -- Subject references ----------------------------------------
        # "chương 4" | "chương nào" | "chương"
        self._add_rule("CHAPTER_REF", ["chương"], weight=1.0, comment="chương")
        self._add_rule("CHAPTER_REF", ["chương", "CHAPTER_NUM"], weight=4.0, comment="chương + số")
        self._add_rule("CHAPTER_REF", ["chương", "WH_QWORD"], weight=1.5, comment="chương nào")

        # "tuần 3" | "tuần nào" | "tuần"
        self._add_rule("WEEK_REF", ["tuần"], weight=1.0, comment="tuần")
        self._add_rule("WEEK_REF", ["tuần", "WEEK_NUM"], weight=4.0, comment="tuần + số")
        self._add_rule("WEEK_REF", ["tuần", "WH_QWORD"], weight=1.5, comment="tuần nào")

        # -- Nominals ---------------------------------------------------
        self._add_rule("NOMINAL", ["NOUN"], weight=3.0, comment="danh từ")
        self._add_rule("NOMINAL", ["NOUN", "NOUN"], weight=1.0, comment="danh từ ghép")
        self._add_rule(
            "NOMINAL", ["NOUN", "TOPIC_NAME"], weight=1.0,
            comment="danh từ + chủ đề ('phần parser')"
        )
        self._add_rule("NOMINAL", ["ADJ", "NOUN"], weight=1.2, comment="danh từ + tính từ")
        self._add_rule("NOMINAL", ["NOUN", "ADJ"], weight=0.8, comment="danh từ + tính từ")
        self._add_rule(
            "NOMINAL", ["NOUN", "WH_QWORD"], weight=1.2, comment="danh từ + từ hỏi"
        )
        self._add_rule(
            "NOMINAL", ["NOUN", "DET"], weight=0.8, comment="danh từ + từ chỉ định ('chương này')"
        )
        self._add_rule(
            "NOMINAL", ["NOUN", "ADV"], weight=0.8, comment="danh từ + trạng ngữ ('chương sau')"
        )

        # -- Domain identifiers ----------------------------------------
        for i in range(1, 13):
            self._add_rule("CHAPTER_NUM", [str(i)], comment="số chương")

        for i in range(1, 16):
            self._add_rule("WEEK_NUM", [str(i)], comment="số tuần")

        for topic in (
            "cfg", "pcfg", "parsing", "semantic", "semantic_grammar", "syntax", "pos",
            "feature", "grammar", "tagging", "disambiguation", "reference",
            "question_answering", "selectional_restriction", "statistical_nlp",
            "python_nlp", "dependency", "discourse", "anaphora", "centering",
            "wsd", "atn", "unification", "lexicon", "top_down", "bottom_up",
            "best_first", "parser",
        ):
            self._add_rule("TOPIC_NAME", [topic], comment="chủ đề NLP")

        for name in ("btl", "bài_tập_lớn", "assignment", "đồ_án"):
            self._add_rule("ASSIGNMENT_NAME", [name], comment="tên bài tập")

        for name in ("llm_rag", "ai"):
            self._add_rule("TECH_NAME", [name], comment="công nghệ được phép dùng")

        for i in range(1, 5):
            for j in range(1, 6):
                if i == 4 and j > 2:
                    break
                self._add_rule("LO_ID", [f"l.o.{i}.{j}"], comment="mã mục tiêu học tập")

        for attribute in ("tín_chỉ", "phút", "midterm", "final"):
            self._add_rule("ATTR_NOUN", [attribute], comment="thuộc tính môn học")

        for roman in ("i", "ii", "iii", "iv"):
            self._add_rule("PART_NUM", [roman], comment="số phần (La Mã)")

        # -- Part of the assignment ------------------------------------
        self._add_rule("PART_REF", ["NOUN", "PART_NUM"], weight=2.0, comment="'phần' + số La Mã")

        # -- Pronouns ---------------------------------------------------
        # NOTE: "chương này" is deliberately absent -- a reference such as
        # "chương này ... chương 10" would name its subject twice.
        for pronoun in ("tôi", "tớ", "mình", "nó", "phần_này"):
            self._add_rule("PRONOUN", [pronoun], comment="đại từ / tham chiếu")

        # -- Determiners ------------------------------------------------
        for det in ("các", "những"):
            self._add_rule("DET", [det], weight=2.0, comment="từ chỉ định")
        for det in ("nào", "gì", "bao", "mấy", "này", "đó"):
            self._add_rule("DET", [det], weight=0.6, comment="từ hỏi")

        # -- Quantifiers ------------------------------------------------
        for quant in ("bao_nhiêu", "mấy"):
            self._add_rule("QUANT", [quant], comment="lượng từ")

        # -- Verbs ------------------------------------------------------
        for verb, weight, comment in [
            ("học", 3.0, "động từ chính"),
            ("nói", 2.5, "động từ chính"),
            ("có", 2.5, "trợ động từ"),
            ("là", 2.0, "trợ động từ"),
            ("xuất", 1.5, "sinh file"),
            ("liên_quan", 1.5, "quan hệ"),
            ("biết", 1.5, "tìm hiểu"),
            ("hỏi", 1.0, "truy vấn"),
            ("tra", 0.3, "động từ - hiếm dùng mở câu hỏi"),
            ("xem", 0.8, "tra cứu"),
            ("tìm", 0.8, "tra cứu"),
            ("yêu_cầu", 1.2, "yêu cầu"),
            ("sử_dụng", 1.2, "sử dụng"),
            ("bao_gồm", 1.0, "gồm"),
            ("trình_bày", 1.2, "trình bày"),
            ("học_về", 1.2, "học về"),
            ("nói_về", 1.5, "nói về"),
            ("gồm", 1.2, "gồm"),
            ("dùng", 1.2, "dùng"),
            ("xây_dựng", 1.2, "xây dựng"),
            ("nằm", 1.0, "nằm ở"),
            ("báo_cáo", 1.0, "báo cáo"),
            ("kéo_dài", 0.8, "kéo dài"),
            ("giới_thiệu", 0.8, "giới thiệu"),
            ("định_nghĩa", 0.8, "định nghĩa"),
        ]:
            self._add_rule("VERB", [verb], weight=weight, comment=comment)

        # -- Auxiliaries (modal verbs) ----------------------------------
        for aux in ("cần", "muốn", "phải", "nên", "được", "sẽ", "bị"):
            self._add_rule("AUX", [aux], comment="trợ động từ")

        # -- Nouns ------------------------------------------------------
        for noun in (
            "tín_chỉ", "môn_học", "chương", "tuần", "bài", "nội_dung",
            "tài_liệu", "quy_định", "deadline", "thời_hạn", "phần",
            "thông_tin", "yêu_cầu", "file", "output", "btl",
            "giữa_kỳ", "cuối_kỳ", "chính_sách", "hỏi_đáp", "lịch_học",
            "phương_pháp", "tham_khảo", "đề_bài", "sử_dụng", "xây_dựng",
            "phần_hẹn", "làm_quen", "học_kỳ", "hạn_nộp", "bài_giảng",
            "ghi_chú", "kiểm_tra", "tiêu_chí", "thành_viên", "nhóm",
        ):
            self._add_rule("NOUN", [noun], comment="danh từ miền")

        # -- Adjectives -------------------------------------------------
        for adj in ("mới", "quan_trọng"):
            self._add_rule("ADJ", [adj], comment="tính từ")

        # -- Verb phrases -----------------------------------------------
        for rhs, weight, comment in [
            (["VERB"], 1.0, "V"),
            (["VERB", "NP"], 4.0, "V NP"),
            (["VERB", "PP"], 3.0, "V PP"),
            (["VERB", "NP", "PP"], 1.5, "V NP PP"),
            (["VERB", "ADV"], 1.0, "V ADV"),
            (["VERB", "NP", "ADV"], 1.5, "V NP ADV"),
            (["VERB", "PP", "ADV"], 1.2, "V PP ADV"),
            (["VERB", "VERB"], 0.8, "V V (nhóm động từ)"),
            (["VERB", "VERB", "NP"], 1.2, "V V NP"),
            (["VERB", "VERB", "PP"], 0.8, "V V PP"),
            (["VERB", "VERB", "PP", "ADV"], 1.0, "V V PP ADV"),
            (["VERB", "VERB", "NP", "ADV"], 1.0, "V V NP ADV"),
            (["VERB", "WH_QWORD"], 3.0, "V + từ hỏi"),
            (["VERB", "WH_QWORD", "NP"], 2.0, "V + từ hỏi + NP"),
            (["VERB", "QUANT", "NP"], 1.0, "V + lượng từ + NP"),
            (["AUX", "VERB"], 1.0, "trợ động từ + V"),
            (["AUX", "VERB", "NP"], 2.0, "trợ động từ + V + NP"),
            (["AUX", "VERB", "PP"], 1.5, "trợ động từ + V + PP"),
            (["AUX", "VERB", "NP", "PP"], 1.0, "trợ động từ + V + NP + PP"),
            (["AUX", "VERB", "NP", "ADV"], 1.5, "trợ động từ + V + NP + ADV"),
            (["AUX", "VERB", "PP", "ADV"], 1.0, "trợ động từ + V + PP + ADV"),
            (["AUX", "VERB", "WH_QWORD"], 1.0, "trợ động từ + V + từ hỏi"),
            (["VERB", "AUX", "VERB", "NP", "ADV"], 1.0,
             "V + trợ động từ + V + NP + ADV ('có được dùng LLM không')"),
            (["VERB", "AUX", "VERB", "NP"], 1.0,
             "V + trợ động từ + V + NP ('có được dùng LLM')"),
            (["QUANT", "NP"], 1.2, "lượng từ + NP"),
        ]:
            self._add_rule("VP", rhs, weight=weight, comment=comment)

        # -- Prepositional phrases --------------------------------------
        self._add_rule("PP", ["PREP", "NP"], weight=3.0, comment="PREP NP")
        self._add_rule("PP", ["PREP", "NOUN"], weight=1.0, comment="PREP NOUN")

        for prep in ("ở", "về", "của", "với", "cho", "vào", "đến", "trong"):
            self._add_rule("PREP", [prep], comment="giới từ")

        # -- Post-modifier sequence -------------------------------------
        self._add_rule("MODS", ["PP"], weight=3.0, comment="một PP hậu tố")
        self._add_rule("MODS", ["PP", "MODS"], weight=1.0, comment="nhiều PP hậu tố")

        # -- Adverbs ----------------------------------------------------
        for adv in ("bao", "nhiêu", "không", "có", "được", "gì"):
            self._add_rule("ADV", [adv], comment="trạng ngữ")
        for adv in ("còn", "rồi", "vậy", "hãy", "sau"):
            self._add_rule("ADV", [adv], weight=0.6, comment="trạng ngữ liên kết")

        # -- Numbers ----------------------------------------------------
        for num in ("1", "2", "3", "4", "5", "6", "7", "8", "9", "10",
                    "11", "12", "13", "14", "15", "30", "60", "90"):
            self._add_rule("NUM", [num], comment="số")

        # -- Punctuation ------------------------------------------------
        self._add_rule("PUNCT", ["?"], weight=10.0, comment="dấu câu hỏi")
        self._add_rule("PUNCT", ["!"], weight=0.3, comment="dấu chấm than")

    # ------------------------------------------------------------------
    # Accessors
    # ------------------------------------------------------------------
    def get_rules(self, lhs: str) -> List[GrammarRule]:
        """All rules for a given non-terminal."""
        return self.rules.get(lhs, [])

    def get_expansions(self, lhs: str) -> List[List[str]]:
        """All possible RHS expansions for a non-terminal."""
        return [rule.rhs for rule in self.get_rules(lhs)]

    def terminals_of(self, lhs: str) -> Set[str]:
        """
        All terminals that the non-terminal ``lhs`` can expand to directly.

        Only productions whose right-hand side is a single terminal are taken
        into account, which makes this a convenient way for the parser to
        discover the vocabulary of a phrase class (e.g. all verbs).
        """
        found: Set[str] = set()
        for rule in self.get_rules(lhs):
            if len(rule.rhs) == 1 and self.is_terminal(rule.rhs[0]):
                found.add(rule.rhs[0])
        return found

    def is_terminal(self, symbol: str) -> bool:
        """True if the symbol is a terminal of this grammar."""
        return symbol in self.terminals or symbol in {"?", "!"}

    def is_nonterminal(self, symbol: str) -> bool:
        """True if the symbol is a non-terminal of this grammar."""
        return symbol in self.nonterminals

    def get_terminal_classes(self) -> Dict[str, str]:
        """
        Map every terminal to its grammar class.

        A non-terminal whose productions are all single terminals defines a
        class, e.g. ``TOPIC_NAME -> 'cfg' | 'pcfg' | ...`` yields the class
        ``TOPIC_NAME`` for those terminals.

        The digits are a special case: ``1`` can be a chapter number *and* a
        week number, so the class cannot be decided from the token alone.
        They are therefore mapped to the generic ``NUM`` class and resolved
        contextually by :meth:`classify_number`.
        """
        if self._terminal_classes is not None:
            return self._terminal_classes

        classes: Dict[str, str] = {}
        for lhs, rules in self.rules.items():
            if lhs in AMBIGUOUS_CLASSES:
                continue
            if all(len(rule.rhs) == 1 and self.is_terminal(rule.rhs[0]) for rule in rules):
                for rule in rules:
                    classes.setdefault(rule.rhs[0], lhs)

        # Terminals that are not covered by a dedicated class fall back to
        # their own name.
        for terminal in self.terminals:
            classes.setdefault(terminal, terminal.upper())

        self._terminal_classes = classes
        return classes

    def classify_number(self, head_noun: str, token: str) -> str:
        """
        Classify a numeric token with respect to its head noun.

        ``("chương", "4")`` -> ``CHAPTER_NUM``, ``("tuần", "3")`` ->
        ``WEEK_NUM``, anything else -> ``NUM``.
        """
        if head_noun == "chương":
            return "CHAPTER_NUM"
        if head_noun == "tuần":
            return "WEEK_NUM"
        return "NUM"

    def get_first_sets(self) -> Dict[str, Set[str]]:
        """Compute the FIRST set of every non-terminal (fixpoint iteration)."""
        if self._first_sets is not None:
            return self._first_sets

        first: Dict[str, Set[str]] = {nt: set() for nt in self.nonterminals}
        for terminal in self.terminals:
            first.setdefault(terminal, {terminal})

        changed = True
        while changed:
            changed = False
            for lhs, rules in self.rules.items():
                for rule in rules:
                    # FIRST of a production is the FIRST of its first symbol
                    # that is able to derive a terminal (or the whole
                    # production is nullable, which never happens here).
                    for symbol in rule.rhs:
                        if self.is_terminal(symbol):
                            new = {symbol}
                        else:
                            new = set(first.get(symbol, set()))
                        if not new:
                            # Nullable symbol -- continue with the next one.
                            continue
                        before = len(first[lhs])
                        first[lhs] |= new
                        if len(first[lhs]) != before:
                            changed = True
                        break

        self._first_sets = first
        return first

    def get_follow_sets(self) -> Dict[str, Set[str]]:
        """Compute the FOLLOW set of every non-terminal (fixpoint iteration)."""
        if self._follow_sets is not None:
            return self._follow_sets

        follow: Dict[str, Set[str]] = {nt: set() for nt in self.nonterminals}
        follow[self.start_symbol] = {"$"}

        changed = True
        while changed:
            changed = False
            for lhs, rules in self.rules.items():
                for rule in rules:
                    for index, symbol in enumerate(rule.rhs):
                        if self.is_terminal(symbol):
                            continue
                        target = follow.setdefault(symbol, set())
                        before = len(target)

                        # Compute the set of terminals that can follow `symbol`.
                        followers = rule.rhs[index + 1:]
                        added: Set[str] = set()
                        if not followers:
                            added |= follow.get(lhs, set())
                        else:
                            first_symbol = followers[0]
                            if self.is_terminal(first_symbol):
                                added.add(first_symbol)
                            else:
                                first_set = self.get_first_sets().get(first_symbol, set())
                                added |= first_set
                                if not first_set:
                                    added |= follow.get(first_symbol, set())

                        target |= added
                        if len(target) != before:
                            changed = True

        self._follow_sets = follow
        return follow

    # ------------------------------------------------------------------
    # Sentence generation
    # ------------------------------------------------------------------
    def _weighted_choice(
        self, rules: List[GrammarRule], rng: Optional[random.Random] = None
    ) -> GrammarRule:
        """Pick a rule proportionally to its weight."""
        rng = rng or self.rng
        weights = [rule.weight for rule in rules]
        if sum(weights) <= 0:
            return rng.choice(rules)
        return rng.choices(rules, weights=weights, k=1)[0]

    def generate_parts(
        self,
        symbol: Optional[str] = None,
        max_depth: int = 20,
        rng: Optional[random.Random] = None,
    ) -> List[str]:
        """Generate a sentence as a list of terminal tokens."""
        if symbol is None:
            symbol = self.start_symbol

        rng = rng or self.rng

        rules = self.get_rules(symbol)
        if not rules:
            return [symbol]
        if max_depth <= 0:
            return [symbol]

        rule = self._weighted_choice(rules, rng)

        parts: List[str] = []
        for sym in rule.rhs:
            if self.is_terminal(sym):
                parts.append(sym)
            else:
                parts.extend(self.generate_parts(sym, max_depth - 1, rng))

        return parts

    def generate_sentence(
        self,
        symbol: Optional[str] = None,
        max_depth: int = 20,
        rng: Optional[random.Random] = None,
    ) -> str:
        """Generate a sentence by recursive weighted expansion."""
        return " ".join(self.generate_parts(symbol, max_depth, rng))

    def _violates_constraints(self, parts: List[str]) -> bool:
        """Check the semantic constraints on the generated token sequence."""
        if not parts:
            return True

        # A sentence must not start with a verb-like terminal.
        if parts[0] in NOT_FIRST:
            return True

        # No two determiners / adjectives / question words in a row.
        terminal_classes = self.get_terminal_classes()
        classes = [terminal_classes.get(part, part.upper()) for part in parts]
        for left, right in zip(classes, classes[1:]):
            if {left, right} in FORBIDDEN_ADJACENT:
                return True

        # A bare number must be preceded by its head noun ("chương 4").
        for index, part in enumerate(parts):
            if part.isdigit():
                if index == 0 or parts[index - 1] not in {"chương", "tuần"}:
                    return True
                # The number must be in range for its head noun.
                value = int(part)
                if parts[index - 1] == "chương" and not 1 <= value <= 12:
                    return True
                if parts[index - 1] == "tuần" and not 1 <= value <= 15:
                    return True

        # The subject noun must not be repeated ("tuần tuần 15", "chương
        # ... ở chương 4") -- a question names its subject exactly once.
        for subject in ("chương", "tuần"):
            if sum(1 for part in parts if part == subject) > 1:
                return True

        # A question word must not open the sentence on its own -- in
        # Vietnamese "gì"/"nào" always follows a verb or a subject noun.
        if parts[0] in {"gì", "nào", "bao_nhiêu", "ở_đâu", "khi_nào"}:
            return True

        # The same applies to a multi-word entity whose first component is a
        # verb ("hỏi đáp") -- it must not open the sentence either.
        if parts[0] in {"hỏi", "làm", "đề", "hỏi_đáp", "làm_quen", "đề_bài"}:
            return True

        # Two question words in a row ("gì nào") are ungrammatical.
        question_words = {"gì", "nào", "bao_nhiêu", "ở_đâu", "khi_nào", "thế_nào", "ai"}
        for left, right in zip(parts, parts[1:]):
            if left in question_words and right in question_words:
                return True

        # A question needs at least one domain identifier (course, chapter,
        # week, topic, assignment or learning outcome) to be meaningful.
        if not any(
            part in DOMAIN_TERMINALS or LO_TERMINAL_RE.match(part)
            for part in parts
        ):
            return True

        # The sentence must end with punctuation.
        if parts[-1] not in {"?", "!"}:
            return True

        return False

    def _is_natural(self, sentence: str) -> bool:
        """Reject sentences that do not read like a Vietnamese question."""
        words = sentence.lower().split()
        if not words:
            return False

        # Too many question words in a row is a sign of a broken derivation.
        question_words = {"mấy", "nào", "gì", "bao", "nhiêu"}
        if sum(1 for w in words if w in question_words) > 2:
            return False

        # A question must contain at least three words.
        if len(words) < 3:
            return False

        return True

    def detokenize(self, sentence: str) -> str:
        """Turn an underscore-joined derivation into readable Vietnamese."""
        result = sentence

        # The longest surface forms must be replaced first, otherwise
        # "bài_tập" would eat the beginning of "bài_tập_lớn".
        for glued, readable in sorted(TOKEN_GLUE.items(), key=lambda kv: -len(kv[0])):
            result = result.replace(glued, readable)

        # Learning-outcome identifiers are written "L.O.2.5".
        result = re.sub(r"\bl\.o\.(\d+(?:\.\d+)?)\b", r"L.O.\1", result)

        # Proper nouns that must keep their canonical capitalisation.
        for lower, canonical in sorted(CAPITALISED_TERMINALS.items(), key=lambda kv: -len(kv[0])):
            result = re.sub(rf"(?<![\w]){re.escape(lower)}(?![\w])", canonical, result)

        # Remove the space in front of punctuation.
        result = re.sub(r"\s+([?.,!])", r"\1", result)
        result = re.sub(r"\s{2,}", " ", result)
        result = result.strip()

        if result:
            result = result[0].upper() + result[1:]

        return result

    def generate_all_sentences(
        self,
        max_sentences: int = 10000,
        max_length: int = 15,
        seed: int = 42,
    ) -> List[str]:
        """
        Generate a deterministic set of well-formed sentences.

        The same ``seed`` always yields the same list, which keeps the
        generated ``output/samples.txt`` reproducible for the demo video.
        """
        rng = random.Random(seed)
        sentences: Set[str] = set()
        attempts = 0
        max_attempts = max_sentences * 60

        while len(sentences) < max_sentences and attempts < max_attempts:
            attempts += 1
            parts = self.generate_parts(self.start_symbol, 20, rng)

            # Structural constraints on the terminal sequence.
            if self._violates_constraints(parts):
                continue
            if parts.count("?") + parts.count("!") != 1:
                continue
            if len(parts) > max_length + 4:
                continue

            sentence = self.detokenize(" ".join(parts))
            if not self._is_natural(sentence):
                continue

            sentences.add(sentence)

        return sorted(sentences)

    # ------------------------------------------------------------------
    # Rendering
    # ------------------------------------------------------------------
    def to_string(self) -> str:
        """Render the grammar for ``output/grammar.txt``."""
        lines: List[str] = []
        lines.append("# ===== COURSE ASSISTANT - CONTEXT-FREE GRAMMAR =====")
        lines.append("# Domain: Vietnamese questions about the NLP course (CO3085)")
        lines.append("# Format: <non-terminal> -> <symbol> ...   [# comment]")
        lines.append("")
        lines.append(f"# Non-terminals ({len(self.nonterminals)}): "
                     + ", ".join(sorted(self.nonterminals)))
        lines.append("")
        lines.append(f"# Terminals ({len(self.terminals)}): "
                     + ", ".join(sorted(self.terminals)))
        lines.append("")

        for lhs in sorted(self.rules.keys()):
            lines.append(f"# --- {lhs} ---")
            for rule in self.rules[lhs]:
                lines.append(rule.to_line())
            lines.append("")

        return "\n".join(lines).rstrip() + "\n"

    def print_grammar(self) -> None:
        """Print the grammar to stdout."""
        print(self.to_string())


# ---------------------------------------------------------------------------
# Template-based questions (a curated, high-quality set)
# ---------------------------------------------------------------------------
COURSE_QUESTION_TEMPLATES = [
    # Course info
    ("Môn {course} có bao nhiêu tín chỉ?", "GET_COURSE_INFO"),
    ("{course} có mấy tín chỉ?", "GET_COURSE_INFO"),
    ("Môn học {course} gồm những phần nào?", "GET_COURSE_INFO"),
    ("{course} có những phần chính nào?", "GET_COURSE_INFO"),
    ("Mô tả môn {course}?", "GET_COURSE_INFO"),
    ("Mục tiêu của môn {course} là gì?", "GET_COURSE_INFO"),
    ("Midterm kéo dài bao lâu?", "GET_COURSE_INFO"),
    ("Final kéo dài bao lâu?", "GET_COURSE_INFO"),
    ("Midterm bao nhiêu phút?", "GET_COURSE_INFO"),
    ("Final bao nhiêu phút?", "GET_COURSE_INFO"),

    # Schedule
    ("Tuần {week} học những gì?", "GET_SCHEDULE"),
    ("Tuần {week} học gì?", "GET_SCHEDULE"),
    ("Hôm nay học gì?", "GET_SCHEDULE"),
    ("Chương {chapter} học vào tuần nào?", "GET_SCHEDULE"),
    ("{topic} được học ở đâu?", "GET_SCHEDULE"),
    ("{topic} được học vào tuần nào?", "GET_SCHEDULE"),
    ("Lịch học tuần {week} là gì?", "GET_SCHEDULE"),

    # Topic
    ("Chương {chapter} nói về gì?", "GET_TOPIC"),
    ("Chương {chapter} có nội dung gì?", "GET_TOPIC"),
    ("Chương {chapter} có những phương pháp gì?", "GET_TOPIC"),
    ("Chương nào học về {topic}?", "GET_TOPIC"),
    ("{topic} nằm ở chương nào?", "GET_TOPIC"),
    ("Chương nào nói về {topic}?", "GET_TOPIC"),
    ("Ai dạy môn {course}?", "GET_INSTRUCTOR"),
    ("Giảng viên phụ trách môn {course} là ai?", "GET_INSTRUCTOR"),

    # Assignment
    ("Bài tập lớn có những yêu cầu gì?", "GET_ASSIGNMENT"),
    ("Bài tập lớn gồm những phần nào?", "GET_ASSIGNMENT"),
    ("Phần {part} của BTL là gì?", "GET_ASSIGNMENT"),
    ("BTL cần xuất những file gì?", "GET_ASSIGNMENT"),
    ("Bài tập lớn có phần parser không?", "GET_ASSIGNMENT"),
    ("Bài tập lớn có phần hỏi đáp không?", "GET_ASSIGNMENT"),

    # Deadline
    ("Deadline BTL là khi nào?", "GET_DEADLINE"),
    ("Thời hạn nộp bài tập lớn là bao giờ?", "GET_DEADLINE"),
    ("Khi nào cần nộp BTL?", "GET_DEADLINE"),

    # Resource
    ("Tài liệu về {topic} ở đâu?", "GET_RESOURCE"),
    ("Có tài liệu nào về {topic} không?", "GET_RESOURCE"),
    ("Sách tham khảo của môn học là gì?", "GET_RESOURCE"),
    ("Tài liệu nào liên quan đến {topic}?", "GET_RESOURCE"),
    ("Tài liệu tham khảo về {topic} là gì?", "GET_RESOURCE"),

    # Rule
    ("Có được sử dụng LLM không?", "GET_RULE"),
    ("Quy định về sử dụng AI là gì?", "GET_RULE"),
    ("Được phép dùng thư viện nào?", "GET_RULE"),
    ("Quy định của môn học là gì?", "GET_RULE"),
    ("Có được dùng LLM/RAG không?", "GET_RULE"),
    ("Quy định về liêm chính học thuật là gì?", "GET_RULE"),

    # Learning outcome
    ("L.O.{lo} là gì?", "GET_LO"),
    ("L.O.{lo} liên quan đến nội dung nào?", "GET_LO"),
    ("L.O.{lo} học về gì?", "GET_LO"),
]


def generate_template_sentences() -> List[Tuple[str, str]]:
    """Expand the curated templates into concrete questions."""
    courses = ["NLP", "CO3085", "xử lý ngôn ngữ tự nhiên"]
    chapters = list(range(1, 13))
    weeks = list(range(1, 16))
    topics = ["CFG", "PCFG", "Parsing", "Semantic", "POS Tagging", "Feature"]
    parts = ["I", "II", "III", "IV"]
    los = ["1.1", "2.1", "2.5", "3.3", "4.1", "4.2"]

    sentences: List[Tuple[str, str]] = []

    for template, intent in COURSE_QUESTION_TEMPLATES:
        try:
            if "{course}" in template:
                for course in courses[:2]:
                    sentences.append((template.format(course=course), intent))
            elif "{chapter}" in template:
                for chapter in chapters[:3]:
                    sentences.append((template.format(chapter=chapter), intent))
            elif "{week}" in template:
                for week in weeks[:3]:
                    sentences.append((template.format(week=week), intent))
            elif "{topic}" in template:
                for topic in topics[:3]:
                    sentences.append((template.format(topic=topic), intent))
            elif "{part}" in template:
                for part in parts[:2]:
                    sentences.append((template.format(part=part), intent))
            elif "{lo}" in template:
                for lo in los[:3]:
                    sentences.append((template.format(lo=lo), intent))
            else:
                sentences.append((template, intent))
        except (KeyError, IndexError, ValueError):
            sentences.append((template, intent))

    return sentences


if __name__ == "__main__":
    grammar = CFG()
    grammar.print_grammar()

    print("\n" + "=" * 50)
    print("Generated sentences:")
    print("=" * 50)

    for index, sentence in enumerate(grammar.generate_all_sentences(max_sentences=30), 1):
        print(f"{index:3}. {sentence}")
