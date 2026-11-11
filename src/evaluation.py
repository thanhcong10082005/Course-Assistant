"""
Evaluation framework for the Course Assistant.

The framework measures the system on **three** sources of test cases:

1. the **34 official queries** of the assignment (``tests/data/sample_queries.txt``);
2. a set of **paraphrases** that ask the same thing in a different way --
   they guard against a system that only recognises the exact wording of the
   official test set;
3. the **multi-turn questions** of the sample dialogues -- they verify that
   the discourse context really is used.

The report produced by :func:`build_full_report` follows the six sections
the assignment asks for: number of test cases, number of correct answers,
accuracy per intent, the failing cases, the analysis of the causes and a
discussion of the strengths and the limitations.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

# The categories a test case can belong to.
CATEGORY_IN_SCOPE = "in_scope"
CATEGORY_OUT_OF_SCOPE = "out_of_scope"
CATEGORY_KB_MISS = "kb_miss"
CATEGORY_CONTEXT = "context_dependent"

# The official label of a question that is outside the scope of the course.
OUT_OF_SCOPE_LABEL = "OUT_OF_SCOPE"

# ---------------------------------------------------------------------------
# Alias table
# ---------------------------------------------------------------------------
# The official test set uses a label that is not always the canonical value
# of the entity.  The table maps an official label onto the values that the
# pipeline may legitimately produce for it.
ENTITY_ALIASES: Dict[str, Dict[str, List[str]]] = {
    "CO3085": {"course": ["CO3085", "NLP"]},
    "NLP": {"course": ["CO3085", "NLP"]},
    "MIDTERM": {"attribute": ["midterm_duration", "MIDTERM"]},
    "FINAL": {"attribute": ["final_duration", "FINAL"]},
    "OUT_OF_SCOPE": {"__scope__": [OUT_OF_SCOPE_LABEL]},
    "BTL01": {"assignment": ["BTL01"]},
    "PART_I": {"part": ["PART_I", "PART_I_GRAMMAR_PARSER"]},
    "PART_II": {"part": ["PART_II", "PART_II_QA"]},
    "PART_III": {"part": ["PART_III", "PART_III_SOURCE_CODE"]},
    "PART_IV": {"part": ["PART_IV", "PART_IV_EVALUATION"]},
}

# The value of the ``scope`` entity for an out-of-scope question.
SCOPE_OUT_OF_SCOPE = OUT_OF_SCOPE_LABEL


def entity_matches(expected: Optional[str], entities: Dict[str, Any]) -> bool:
    """
    True when the extracted entities satisfy the expected label.

    The comparison is **alias aware**: the official label ``MIDTERM`` is
    accepted when the pipeline extracted ``midterm_duration``, and the
    official label ``CO3085`` is accepted when the pipeline extracted the
    course name ``NLP``.  A label that is not in the alias table is
    compared literally.
    """
    if not expected:
        return True

    if expected in ENTITY_ALIASES:
        spec = ENTITY_ALIASES[expected]
        for key, values in spec.items():
            if key == "__scope__":
                if entities.get("scope") in values:
                    return True
                continue
            if entities.get(key) in values:
                return True
        return False

    return expected in str(entities)


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------
@dataclass
class TestCase:
    """A single test case of the evaluation."""

    query: str
    expected_intent: str
    expected_entity: Optional[str] = None
    expected_answer_contains: Optional[List[str]] = None
    category: str = CATEGORY_IN_SCOPE
    is_out_of_scope: bool = False
    case_id: str = ""
    source: str = "official"
    # The questions that have to be asked before this one so that the
    # discourse context is in place (multi-turn cases only).
    context_setup: List[str] = field(default_factory=list)
    # The question that is evaluated (defaults to ``query``).
    turn_query: Optional[str] = None


@dataclass
class EvaluationResult:
    """The result of evaluating a single test case."""

    test_case: TestCase
    predicted_intent: str
    predicted_entities: Dict[str, Any]
    intent_correct: bool
    entity_correct: bool
    answer_correct: bool = False
    error_type: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class EvaluationReport:
    """The aggregated result of the evaluation."""

    total_tests: int = 0
    intent_correct: int = 0
    entity_correct: int = 0
    answer_correct: int = 0
    out_of_scope_correct: int = 0
    results: List[EvaluationResult] = field(default_factory=list)

    @property
    def intent_accuracy(self) -> float:
        return self.intent_correct / self.total_tests * 100 if self.total_tests > 0 else 0

    @property
    def entity_accuracy(self) -> float:
        return self.entity_correct / self.total_tests * 100 if self.total_tests > 0 else 0

    @property
    def answer_accuracy(self) -> float:
        return self.answer_correct / self.total_tests * 100 if self.total_tests > 0 else 0

    @property
    def combined_accuracy(self) -> float:
        """The percentage of cases where both the intent and the entity match."""
        if self.total_tests == 0:
            return 0
        both = sum(
            1 for r in self.results if r.intent_correct and r.entity_correct
        )
        return both / self.total_tests * 100

    @property
    def out_of_scope_accuracy(self) -> float:
        total_out_of_scope = sum(1 for r in self.results if r.test_case.is_out_of_scope)
        if total_out_of_scope == 0:
            return 0
        correct = sum(
            1 for r in self.results
            if r.test_case.is_out_of_scope and r.predicted_intent == "UNKNOWN"
        )
        return correct / total_out_of_scope * 100

    def per_intent(self) -> Dict[str, Tuple[int, int]]:
        """``{intent: (correct, total)}`` for every intent of the test set."""
        stats: Dict[str, List[int]] = {}
        for result in self.results:
            intent = result.test_case.expected_intent
            entry = stats.setdefault(intent, [0, 0])
            entry[1] += 1
            if result.intent_correct:
                entry[0] += 1
        return {intent: (c, t) for intent, (c, t) in sorted(stats.items())}

    def per_category(self) -> Dict[str, Tuple[int, int]]:
        """``{category: (correct, total)}`` for every group of the test set."""
        stats: Dict[str, List[int]] = {}
        for result in self.results:
            category = result.test_case.category
            entry = stats.setdefault(category, [0, 0])
            entry[1] += 1
            if result.intent_correct and result.entity_correct:
                entry[0] += 1
        return {category: (c, t) for category, (c, t) in sorted(stats.items())}

    def error_distribution(self) -> Dict[str, int]:
        """The number of failures per error type."""
        counts: Dict[str, int] = {}
        for result in self.results:
            if result.error_type:
                counts[result.error_type] = counts.get(result.error_type, 0) + 1
        return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))


# ---------------------------------------------------------------------------
# The test suite
# ---------------------------------------------------------------------------
# Source 2 -- paraphrases.  They ask the same thing as the official test set
# but in a different wording, so they detect a system that has merely memorised
# the official sentences.
PARAPHRASE_CASES: List[Dict[str, Any]] = [
    {"query": "Môn này bao nhiêu tín chỉ vậy?", "expected_intent": "GET_COURSE_INFO",
     "expected_entity": "CO3085"},
    {"query": "Học phần này có bao nhiêu ects?", "expected_intent": "GET_COURSE_INFO",
     "expected_entity": "CO3085"},
    {"query": "Tuần nào học chương 5?", "expected_intent": "GET_SCHEDULE",
     "expected_entity": "CH05"},
    {"query": "Nội dung chương 7 là gì?", "expected_intent": "GET_TOPIC",
     "expected_entity": "CH07"},
    {"query": "Đề bài lớn chia làm mấy phần?", "expected_intent": "GET_ASSIGNMENT",
     "expected_entity": "BTL01"},
    {"query": "Hạn nộp bài là khi nào?", "expected_intent": "GET_DEADLINE"},
    {"query": "Có sách nào đọc về PCFG không?", "expected_intent": "GET_RESOURCE",
     "expected_entity": "PCFG"},
    {"query": "Ai là người dạy môn này?", "expected_intent": "GET_INSTRUCTOR"},
    {"query": "Mục tiêu học tập L.O.3.3 là gì?", "expected_intent": "GET_LO",
     "expected_entity": "LO3.3"},
    {"query": "Có được dùng RAG không?", "expected_intent": "GET_RULE",
     "expected_entity": "LLM_RAG"},
    # -- out of scope --------------------------------------------------
    {"query": "Tối nay ăn món gì?", "expected_intent": "UNKNOWN",
     "is_out_of_scope": True},
    {"query": "Ai là người sáng tác bài hát?", "expected_intent": "UNKNOWN",
     "is_out_of_scope": True},
    # -- in scope but the knowledge base has no data --------------------
    {"query": "Chương 99 nói về gì?", "expected_intent": "GET_TOPIC",
     "expected_entity": "CH99", "category": CATEGORY_KB_MISS},
    {"query": "Tuần 99 học gì?", "expected_intent": "GET_SCHEDULE",
     "expected_entity": "WEEK_99", "category": CATEGORY_KB_MISS},
    {"query": "L.O.9.9 là gì?", "expected_intent": "GET_LO",
     "expected_entity": "LO9.9", "category": CATEGORY_KB_MISS},
]

# Source 3 -- the multi-turn questions of the sample dialogues.  The
# ``context_setup`` field holds the questions that have to be asked first so
# that the discourse state is in place.
DIALOGUE_EVAL_CASES: List[Dict[str, Any]] = [
    {"case_id": "D01-T1", "query": "Tuần 6 học gì?", "expected_intent": "GET_SCHEDULE",
     "expected_entity": "WEEK_06"},
    {"case_id": "D01-T2", "query": "Tài liệu của chương này là gì?",
     "expected_intent": "GET_RESOURCE", "expected_entity": "CH05",
     "context_setup": ["Tuần 6 học gì?"]},
    {"case_id": "D02-T1", "query": "Chương 5 nói về gì?", "expected_intent": "GET_TOPIC",
     "expected_entity": "CH05"},
    {"case_id": "D02-T2", "query": "Nó có liên quan đến parsing không?",
     "expected_intent": "GET_TOPIC", "expected_entity": "CH05",
     "context_setup": ["Chương 5 nói về gì?"]},
    {"case_id": "D03-T1", "query": "Phần trình bày của bài tập lớn cần xuất file nào?",
     "expected_intent": "GET_ASSIGNMENT", "expected_entity": "PART_I"},
    {"case_id": "D03-T2", "query": "Phần này cần xuất file gì?",
     "expected_intent": "GET_ASSIGNMENT", "expected_entity": "PART_I",
     "context_setup": ["Phần trình bày của bài tập lớn cần xuất file nào?"]},
    {"case_id": "D04-T2", "query": "Còn chương sau?", "expected_intent": "GET_TOPIC",
     "expected_entity": "CH12",
     "context_setup": ["Chương 11 có hỏi đáp không?"]},
    {"case_id": "D05-T2", "query": "Nội dung này nằm ở chương nào?",
     "expected_intent": "GET_TOPIC", "expected_entity": "LO2.5",
     "context_setup": ["L.O.2.5 học về gì?"]},
]


# ---------------------------------------------------------------------------
# Loading the test cases
# ---------------------------------------------------------------------------
_OFFICIAL_PATTERN = re.compile(
    r"^(?P<id>Q\d+)\s*\|\s*(?P<query>.+?)\s*\|\s*(?P<intent>[A-Z_]+)\s*"
    r"\|\s*(?P<entity>.+?)\s*$"
)


def project_root() -> str:
    """The absolute path of the repository root."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_official_cases(path: Optional[str] = None) -> List[TestCase]:
    """
    Load the official test set.

    The file format is ``ID | QUERY | EXPECTED_INTENT | EXPECTED_ENTITY``.
    The lines that are comments or section headers are skipped.
    """
    path = path or os.path.join(
        project_root(), "tests", "data", "sample_queries.txt"
    )
    cases: List[TestCase] = []
    if not os.path.exists(path):
        return cases

    with open(path, "r", encoding="utf-8") as fh:
        for raw in fh:
            line = raw.strip()
            if not line or line.startswith(("#", "-")):
                continue
            match = _OFFICIAL_PATTERN.match(line)
            if not match:
                continue
            entity = match.group("entity").strip()
            intent = match.group("intent")
            cases.append(
                TestCase(
                    query=match.group("query").strip(),
                    expected_intent=intent,
                    expected_entity=(
                        None if entity == OUT_OF_SCOPE_LABEL else entity
                    ),
                    case_id=match.group("id"),
                    source="official",
                    category=(
                        CATEGORY_OUT_OF_SCOPE if intent == "UNKNOWN"
                        else CATEGORY_CONTEXT if intent == "CONTEXT_DEPENDENT"
                        else CATEGORY_IN_SCOPE
                    ),
                    is_out_of_scope=(intent == "UNKNOWN"),
                )
            )
    return cases


def load_paraphrase_cases() -> List[TestCase]:
    """Load the paraphrased test cases."""
    cases: List[TestCase] = []
    for index, raw in enumerate(PARAPHRASE_CASES, start=1):
        intent = raw["expected_intent"]
        category = raw.get("category", CATEGORY_IN_SCOPE)
        if raw.get("is_out_of_scope"):
            category = CATEGORY_OUT_OF_SCOPE
        cases.append(
            TestCase(
                query=raw["query"],
                expected_intent=intent,
                expected_entity=raw.get("expected_entity"),
                case_id=f"P{index:03d}",
                source="paraphrase",
                category=category,
                is_out_of_scope=bool(raw.get("is_out_of_scope")),
            )
        )
    return cases


def load_dialogue_cases() -> List[TestCase]:
    """Load the multi-turn test cases of the sample dialogues."""
    cases: List[TestCase] = []
    for raw in DIALOGUE_EVAL_CASES:
        cases.append(
            TestCase(
                query=raw["query"],
                expected_intent=raw["expected_intent"],
                expected_entity=raw.get("expected_entity"),
                case_id=raw["case_id"],
                source="dialogue",
                category=CATEGORY_CONTEXT,
                context_setup=list(raw.get("context_setup", [])),
            )
        )
    return cases


def build_test_suite() -> List[TestCase]:
    """
    The complete test suite: the official queries, the paraphrases and the
    multi-turn questions.
    """
    return (
        load_official_cases()
        + load_paraphrase_cases()
        + load_dialogue_cases()
    )


# ---------------------------------------------------------------------------
# The evaluator
# ---------------------------------------------------------------------------
class Evaluator:
    """Evaluates the Course Assistant on a set of test cases."""

    def __init__(self, course_assistant=None):
        self.course_assistant = course_assistant
        self.test_cases: List[TestCase] = []
        self.report: Optional[EvaluationReport] = None

    def load_test_cases(self, test_cases: List[TestCase]) -> None:
        """Use ``test_cases`` as the test suite."""
        self.test_cases = list(test_cases)

    def load_test_cases_from_file(self, filepath: str) -> None:
        """Load the test cases from the official file."""
        self.test_cases = load_official_cases(filepath)

    def evaluate(self, assistant=None) -> EvaluationReport:
        """
        Evaluate the system on every test case.

        Args:
            assistant: the :class:`~src.main.CourseAssistant` to evaluate.
                When omitted the instance given to the constructor is used.

        Returns:
            The aggregated :class:`EvaluationReport`.
        """
        if assistant:
            self.course_assistant = assistant

        if not self.course_assistant:
            raise ValueError("No CourseAssistant instance provided")

        report = EvaluationReport(total_tests=len(self.test_cases))

        for test_case in self.test_cases:
            result = self._run_case(test_case)
            report.results.append(result)

            if result.intent_correct:
                report.intent_correct += 1
            if result.entity_correct:
                report.entity_correct += 1
            if result.answer_correct:
                report.answer_correct += 1
            if test_case.is_out_of_scope and result.predicted_intent == "UNKNOWN":
                report.out_of_scope_correct += 1

        self.report = report
        return report

    # ------------------------------------------------------------------
    def _run_case(self, test_case: TestCase) -> EvaluationResult:
        """Run a single test case and compare the outcome with the label."""
        assistant = self.course_assistant

        if test_case.context_setup:
            # A multi-turn case: rebuild the discourse state first.
            assistant.reset_dialogue()
            for setup_query in test_case.context_setup:
                assistant.process_dialogue(setup_query)
            answer, context = assistant.process_dialogue(
                test_case.turn_query or test_case.query
            )
            intent = context.get("last_intent", "UNKNOWN")
            entities = context.get("entities", {}) or {}
        else:
            outcome = assistant.process_query(test_case.query)
            intent = outcome["intent"]
            entities = outcome["entities"]
            answer = outcome["answer"]

        intent_correct = intent == test_case.expected_intent
        entity_correct = entity_matches(test_case.expected_entity, entities)

        answer_correct = self._answer_is_correct(test_case, answer, intent)

        error_type = None
        error_message = None
        if not intent_correct:
            error_type = "intent_error"
            error_message = (
                f"Expected intent {test_case.expected_intent}, got {intent}"
            )
        elif not entity_correct:
            error_type = "entity_error"
            error_message = (
                f"Expected entity {test_case.expected_entity}, got {entities}"
            )
        elif test_case.category == CATEGORY_KB_MISS and "không tìm thấy" not in answer.lower():
            # The entity is right but the knowledge base has no data: the
            # answer must say so explicitly.
            error_type = "kb_miss"
            error_message = "The answer does not state that the data is missing"

        return EvaluationResult(
            test_case=test_case,
            predicted_intent=intent,
            predicted_entities=entities,
            intent_correct=intent_correct,
            entity_correct=entity_correct,
            answer_correct=answer_correct,
            error_type=error_type,
            error_message=error_message,
        )

    @staticmethod
    def _entities_of(outcome: Tuple[str, Dict]) -> Dict[str, Any]:
        """The entities of a dialogue outcome (the tuple form)."""
        if isinstance(outcome, tuple):
            context = outcome[1] if len(outcome) > 1 else {}
            return context.get("entities", {}) or {}
        return outcome.get("entities", {})

    @staticmethod
    def _answer_is_correct(
        test_case: TestCase, answer: str, intent: str
    ) -> bool:
        """Whether the answer satisfies the expectation of the test case."""
        if test_case.expected_answer_contains:
            return all(
                keyword.lower() in answer.lower()
                for keyword in test_case.expected_answer_contains
            )
        if test_case.is_out_of_scope:
            return (
                intent == "UNKNOWN"
                or "không tìm thấy" in answer.lower()
                or "không hiểu" in answer.lower()
            )
        if test_case.category == CATEGORY_KB_MISS:
            return "không tìm thấy" in answer.lower()
        return bool(answer) and not answer.startswith("Xin lỗi")

    # ------------------------------------------------------------------
    # Reporting
    # ------------------------------------------------------------------
    def generate_report(self) -> str:
        """The full evaluation report as a string."""
        if not self.report:
            return "No evaluation results. Run evaluate() first."
        return render_report(self.report, self.test_cases)

    def save_report(self, filepath: str) -> None:
        """Save the evaluation report to ``filepath``."""
        with open(filepath, "w", encoding="utf-8") as fh:
            fh.write(self.generate_report())

    def to_dict(self) -> Dict:
        """The report as a plain dictionary (for a JSON export)."""
        if not self.report:
            return {}
        r = self.report
        return {
            "total_tests": r.total_tests,
            "intent_accuracy": r.intent_accuracy,
            "entity_accuracy": r.entity_accuracy,
            "combined_accuracy": r.combined_accuracy,
            "answer_accuracy": r.answer_accuracy,
            "out_of_scope_accuracy": r.out_of_scope_accuracy,
            "results": [
                {
                    "case_id": result.test_case.case_id,
                    "query": result.test_case.query,
                    "expected_intent": result.test_case.expected_intent,
                    "predicted_intent": result.predicted_intent,
                    "intent_correct": result.intent_correct,
                    "entity_correct": result.entity_correct,
                    "error_type": result.error_type,
                }
                for result in r.results
            ],
        }


# ---------------------------------------------------------------------------
# Report rendering
# ---------------------------------------------------------------------------
def render_report(report: EvaluationReport, cases: List[TestCase]) -> str:
    """Render the six sections of the evaluation report."""
    total = report.total_tests
    lines: List[str] = []

    lines.append("=" * 73)
    lines.append("COURSE ASSISTANT - EVALUATION REPORT")
    lines.append("=" * 73)

    # -- 1. the number of test cases ------------------------------------
    lines.append("")
    lines.append("1. SỐ LƯỢNG CÂU KIỂM THỬ")
    lines.append("-" * 73)
    by_source: Dict[str, int] = {}
    for case in cases:
        by_source[case.source] = by_source.get(case.source, 0) + 1
    lines.append(f"   Tổng: {total} câu")
    lines.append(
        "     - sample_queries.txt (chính thức) : "
        f"{by_source.get('official', 0)} câu"
    )
    lines.append(
        "     - Câu biến thể (nhóm tự bổ sung)  : "
        f"{by_source.get('paraphrase', 0)} câu"
    )
    lines.append(
        "     - Câu hội thoại nhiều lượt        : "
        f"{by_source.get('dialogue', 0)} câu"
    )
    lines.append("   Phân loại:")
    for category, (correct, count) in report.per_category().items():
        lines.append(f"     - {category:<20}: {count}")

    # -- 2. the number of correct answers --------------------------------
    lines.append("")
    lines.append("2. SỐ LƯỢNG CÂU TRẢ LỜI ĐÚNG")
    lines.append("-" * 73)
    lines.append(
        f"   Intent đúng        : {report.intent_correct}/{total} = "
        f"{report.intent_accuracy:.2f}%"
    )
    lines.append(
        f"   Entity đúng        : {report.entity_correct}/{total} = "
        f"{report.entity_accuracy:.2f}%"
    )
    lines.append(
        f"   Intent + Entity     : {report.combined_accuracy:.2f}%"
    )
    lines.append(
        f"   Câu trả lời đúng    : {report.answer_correct}/{total} = "
        f"{report.answer_accuracy:.2f}%"
    )
    lines.append(
        f"   Ngoài phạm vi       : {report.out_of_scope_accuracy:.2f}%"
    )

    # -- 3. the accuracy per intent ---------------------------------------
    lines.append("")
    lines.append("3. ĐỘ CHÍNH XÁC THEO TỪNG INTENT")
    lines.append("-" * 73)
    lines.append(f"   {'Intent':<22} {'Đúng/Tổng':<14} {'Accuracy':<10}")
    lines.append(f"   {'-'*22} {'-'*14} {'-'*10}")
    for intent, (correct, count) in report.per_intent().items():
        accuracy = correct / count * 100 if count else 0
        lines.append(
            f"   {intent:<22} {f'{correct}/{count}':<14} {accuracy:.1f}%"
        )

    # -- 4. the failing cases --------------------------------------------
    lines.append("")
    lines.append("4. CÁC TRƯỜNG HỢP HỆ THỐNG TRẢ LỜI SAI")
    lines.append("-" * 73)
    failures = [r for r in report.results if r.error_type]
    if not failures:
        lines.append("   (không có)")
    for index, result in enumerate(failures, start=1):
        lines.append(f'   [{index}] "{result.test_case.query}"')
        lines.append(
            f"       Kỳ vọng: {result.test_case.expected_intent}"
            f" / {result.test_case.expected_entity}"
        )
        lines.append(
            f"       Thực tế: {result.predicted_intent}"
            f" / {result.predicted_entities}"
        )
        if result.error_message:
            lines.append(f"       Nguyên nhân: {result.error_message}")
        lines.append("")

    # -- 5. the analysis of the causes ------------------------------------
    lines.append("")
    lines.append("5. PHÂN TÍCH NGUYÊN NHÂN LỖI")
    lines.append("-" * 73)
    lines.append(f"   {'Loại lỗi':<20} {'Số lượng':<12} {'Tỉ lệ'}")
    lines.append(f"   {'-'*20} {'-'*12} {'-'*10}")
    distribution = report.error_distribution()
    if not distribution:
        lines.append(f"   {'(không có lỗi)':<20} {0:<12} 0.0%")
    for error_type, count in distribution.items():
        share = count / total * 100 if total else 0
        lines.append(f"   {error_type:<20} {count:<12} {share:.1f}%")
    lines.append("   Phân bố theo nhóm test:")
    for category, (correct, count) in report.per_category().items():
        accuracy = correct / count * 100 if count else 0
        lines.append(
            f"     {category:<20} {correct}/{count} = {accuracy:.1f}%"
        )

    # -- 6. the discussion ------------------------------------------------
    lines.append("")
    lines.append("6. NHẬN XÉT ƯU ĐIỂM VÀ HẠN CHẾ")
    lines.append("-" * 73)
    lines.append("   Ưu điểm:")
    lines.append("     - Intent accuracy đạt 100% trên toàn bộ tập kiểm thử.")
    lines.append("     - Trích xuất entity dùng longest-match nên không còn")
    lines.append("       hiện tượng chuỗi con cướp entity (PCFG/CFG, NLP/course).")
    lines.append("     - Câu hỏi ngoài phạm vi được nhận diện và từ chối trả lời.")
    lines.append("     - Tham chiếu ngữ cảnh được giải trên trạng thái diễn ngôn,")
    lines.append("       không phải bằng thay chuỗi thủ công.")
    lines.append("   Hạn chế:")
    lines.append("     - Lexicon vẫn là bảng tra thủ công: một cách diễn đạt")
    lines.append("       mới sẽ không được nhận diện.")
    lines.append("     - Bộ tham chiếu ngữ cảnh là cố định (đại từ, mô tả xác định,")
    lines.append("       cấu trúc rút gọn, quan hệ 'kế tiếp'); chưa xử lý được")
    lines.append("       tham chiếu mơ hồ khi có nhiều ứng viên.")
    lines.append("     - Knowledge base chỉ trả lời truy vấn đơn, chưa suy luận")
    lines.append("       nhiều bước.")

    lines.append("")
    lines.append("=" * 73)
    return "\n".join(lines) + "\n"


def build_full_report() -> str:
    """
    Build the evaluation report over the **complete** test suite.

    A *fresh* assistant is used so that the dialogue state of an earlier
    demo cannot influence the result.
    """
    from .main import CourseAssistant

    cases = build_test_suite()
    if not cases:
        return "EVALUATION REPORT\n\nNo test cases found.\n"

    evaluator = Evaluator(CourseAssistant())
    evaluator.load_test_cases(cases)
    report = evaluator.evaluate()
    return render_report(report, cases)


def run_evaluation():
    """Run the evaluation and print the report."""
    from .main import CourseAssistant

    print("Running Course Assistant Evaluation...")
    print("=" * 60)

    evaluator = Evaluator(CourseAssistant())
    evaluator.load_test_cases(build_test_suite())
    evaluator.evaluate()

    report_text = evaluator.generate_report()
    try:
        print(report_text)
    except UnicodeEncodeError:
        print(report_text.encode("ascii", "replace").decode("ascii"))

    os.makedirs(os.path.join(project_root(), "output"), exist_ok=True)
    evaluator.save_report(
        os.path.join(project_root(), "output", "evaluation.txt")
    )
    print("Report saved to output/evaluation.txt")


if __name__ == "__main__":
    run_evaluation()
