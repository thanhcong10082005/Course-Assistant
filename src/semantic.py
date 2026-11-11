"""
Semantic Representation module for Course Assistant.

Lexicon-driven analysis
-----------------------
The semantic analyzer is built on top of :mod:`src.lexicon` instead of
ad-hoc regexes and keyword lists that lived *next to* the domain lexicon.
The consequences of the old design were visible in the metrics:

* a topic could be stolen by a shorter substring ("PCFG" -> "CFG",
  "semantic grammar" -> "semantic", "statistical NLP" -> "NLP"),
* the intent of a query could not be refined (a request to *solve* an
  exercise was answered as a question about the assignment),
* a query that only makes sense in the context of the previous turn was
  answered with a confident but wrong answer.

The analyzer implemented here

* resolves the entities through :mod:`src.lexicon`, which applies a
  **longest-match** strategy so that a longer surface always wins over a
  shorter one that is contained in it,
* derives the *part of the assignment* from the topic of the question
  ("parser" -> Part I, "hỏi đáp" -> Part II),
* knows when a query is **out of scope** and answers "UNKNOWN" instead of
  guessing, and
* knows when a query is **context dependent** (``CONTEXT_DEPENDENT``) so
  that the pipeline can ask for clarification instead of inventing an
  answer.
"""

import re
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

from .lexicon import Lexicon, get_lexicon


class IntentType(Enum):
    """Enumeration of intent types"""
    GET_COURSE_INFO = "GET_COURSE_INFO"
    GET_SCHEDULE = "GET_SCHEDULE"
    GET_TOPIC = "GET_TOPIC"
    GET_ASSIGNMENT = "GET_ASSIGNMENT"
    GET_DEADLINE = "GET_DEADLINE"
    GET_RESOURCE = "GET_RESOURCE"
    GET_RULE = "GET_RULE"
    GET_INSTRUCTOR = "GET_INSTRUCTOR"
    GET_LO = "GET_LO"
    CONTEXT_DEPENDENT = "CONTEXT_DEPENDENT"
    UNKNOWN = "UNKNOWN"


@dataclass
class Entity:
    """Represents an extracted entity"""
    type: str
    value: str
    original: str
    normalized: str


@dataclass
class SemanticRepresentation:
    """
    Semantic representation of a user query
    Contains intent, entities, and semantic structure
    """
    intent: IntentType
    entities: Dict[str, Any] = field(default_factory=dict)
    attributes: Dict[str, bool] = field(default_factory=dict)
    query_type: str = ""
    raw_query: str = ""

    def to_logical_form(self) -> str:
        """Convert to logical form string"""
        if self.entities:
            entity_str = ", ".join(f"{k}={v}" for k, v in self.entities.items())
        else:
            entity_str = ""

        return f"{self.intent.value}({entity_str})"

    def __str__(self):
        return self.to_logical_form()

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'intent': self.intent.value,
            'entities': self.entities,
            'attributes': self.attributes,
            'query_type': self.query_type,
            'raw_query': self.raw_query
        }


# ---------------------------------------------------------------------------
# Intent rules
# ---------------------------------------------------------------------------
# Each rule is (intent, regex, score).  The rules are evaluated against the
# normalized query; the intent with the highest score wins.  A score of 0
# means "never selected on its own".
INTENT_RULES: List[Tuple[IntentType, str, int]] = [
    # -- very specific markers ------------------------------------------
    (IntentType.GET_LO, r"\blo_\d", 100),
    (IntentType.GET_DEADLINE, r"\bdeadline\b", 90),
    (IntentType.GET_DEADLINE, r"thời hạn|hạn nộp", 90),
    (IntentType.GET_DEADLINE, r"khi nào nộp|nộp bài tập|nộp btl", 90),
    (IntentType.GET_DEADLINE, r"khi nào|bao giờ", 55),

    (IntentType.GET_INSTRUCTOR, r"ai dạy|ai giảng|giảng viên|ai là người", 90),

    (IntentType.GET_RULE, r"quy định", 80),
    (IntentType.GET_RULE, r"được phép dùng|được dùng|cho phép", 85),
    (IntentType.GET_RULE, r"sử dụng ai|dùng ai|dùng llm|sử dụng llm|dùng llm", 85),
    (IntentType.GET_RULE, r"chính sách|liêm chính|academic integrity", 80),
    (IntentType.GET_RULE, r"\brule\b|\bregulation\b|\bpolicy\b", 80),

    (IntentType.GET_RESOURCE, r"tài liệu|tai lieu", 80),
    (IntentType.GET_RESOURCE, r"sách|giáo trình|giao trinh|tham khảo", 80),
    (IntentType.GET_RESOURCE, r"\bresource\b|\bbook\b|\bslides?\b", 80),

    (IntentType.GET_ASSIGNMENT, r"bài tập lớn|bài tap lon", 75),
    (IntentType.GET_ASSIGNMENT, r"\bbtl\b|\bđồ án\b|assignment", 75),
    (IntentType.GET_ASSIGNMENT, r"xuất file|file gì|output file", 60),

    (IntentType.GET_SCHEDULE, r"tuần\s*\d+", 70),
    (IntentType.GET_SCHEDULE, r"lịch học|kế hoạch học|hôm nay học", 80),
    (IntentType.GET_SCHEDULE, r"(chương|ch)\s*\d*\s*.*tuần nào", 95),
    (IntentType.GET_SCHEDULE, r"(học|dạy|trình bày).*(ở|vào)\s*tuần nào", 95),
    (IntentType.GET_SCHEDULE, r"tuần nào\s*(học|dạy|trình bày|được học|chương)", 95),
    (IntentType.GET_SCHEDULE, r"được học ở tuần nào", 95),
    (IntentType.GET_SCHEDULE, r"học ở tuần", 85),
    (IntentType.GET_SCHEDULE, r"tuần nào", 60),

    (IntentType.GET_TOPIC, r"chương nào", 85),
    (IntentType.GET_TOPIC, r"chương\s*\d+", 70),
    (IntentType.GET_TOPIC, r"nói về|nội dung gì|chủ đề", 70),
    (IntentType.GET_TOPIC, r"có những phương pháp|phương pháp gì", 65),
    (IntentType.GET_TOPIC, r"liên quan đến|liên quan với", 55),
    (IntentType.GET_TOPIC, r"được học ở đâu|học ở đâu", 60),

    (IntentType.GET_COURSE_INFO, r"tín chỉ|tín chỉ", 80),
    (IntentType.GET_COURSE_INFO, r"\bects\b", 80),
    (IntentType.GET_COURSE_INFO, r"mục tiêu", 75),
    (IntentType.GET_COURSE_INFO, r"mô tả|giới thiệu môn", 75),
    (IntentType.GET_COURSE_INFO, r"midterm|giữa kỳ", 85),
    (IntentType.GET_COURSE_INFO, r"\bfinal\b|cuối kỳ", 85),
    (IntentType.GET_COURSE_INFO, r"gồm những phần|phần chính|cấu trúc", 75),
    (IntentType.GET_COURSE_INFO, r"môn học gồm|môn.*gồm những", 75),
]


class SemanticAnalyzer:
    """
    Analyzes parsed sentences and converts them to semantic representations.

    The analyzer is driven by the domain lexicon (:mod:`src.lexicon`); the
    keyword lists below only describe the *intent* patterns, not the entity
    vocabulary.
    """

    def __init__(self, lexicon: Optional[Lexicon] = None):
        self.lexicon = lexicon if lexicon is not None else get_lexicon()

        # The group that holds the surface forms of the assignment parts.
        self.part_group = "part_of_assignment"

    # ------------------------------------------------------------------
    # Normalisation
    # ------------------------------------------------------------------
    def normalize_text(self, text: str) -> str:
        """Normalize text for pattern matching"""
        # Lowercase and replace spaces with underscores
        text = text.lower().strip()
        # Preserve L.O.X.Y patterns: replace "l.o.X.Y" with "lo_X_Y"
        text = re.sub(r'l\.o\.(\d+)\.(\d+)', r'lo_\1_\2', text)
        # Replace "l.o.X" with "lo_X" (single level)
        text = re.sub(r'l\.o\.(\d+)(?!\.)', r'lo_\1', text)
        # Replace "LO2.5" / "LO2_5" with the canonical "lo_2_5"
        text = re.sub(r'\blo(\d+)[._](\d+)', r'lo_\1_\2', text)
        text = re.sub(r'\blo(\d+)\b', r'lo_\1', text)
        # Normalise the punctuation-bearing surfaces.
        text = text.replace("llm/rag", "llm rag").replace("q&a", "qa")
        text = text.replace("tp.hcm", "tp hcm")
        # Remove remaining punctuation
        text = text.replace('?', '').replace('.', '').replace(',', '')
        # Normalize spaces
        text = ' '.join(text.split())
        return text

    # ------------------------------------------------------------------
    # Intent
    # ------------------------------------------------------------------
    def extract_intent(
        self,
        text: str,
        tokens: Optional[List[str]] = None,
        entities: Optional[Dict[str, Any]] = None,
    ) -> IntentType:
        """
        Extract the intent of the query.

        The rules are evaluated in the order of the assignment's weight;
        the highest score wins.  An explicit out-of-scope check runs first
        so that a request such as "Hãy giải bài tập xác suất này giúp tôi"
        is never mistaken for a question about the assignment.
        """
        normalized = self.normalize_text(text)
        entities = entities if entities is not None else {}

        # -- out of scope ------------------------------------------------
        if self.lexicon.is_out_of_scope(normalized):
            return IntentType.UNKNOWN

        # An explicit "solve this for me" request is out of scope even when
        # the sentence also mentions the assignment.
        if re.search(r"giải (bài tập|đề|bài)(?! lớn)", normalized):
            return IntentType.UNKNOWN
        if re.search(r"(làm hộ|viết code cho tôi|dịch (văn bản|sang))", normalized):
            return IntentType.UNKNOWN

        scores: Dict[IntentType, int] = {}
        for intent, pattern, score in INTENT_RULES:
            if re.search(pattern, normalized):
                scores[intent] = scores.get(intent, 0) + score

        # -- tie-breaking rules based on the extracted entities -----------
        # A question about a chapter / topic is a topic question unless it
        # explicitly asks for a resource ("tài liệu về X") or for a rule.
        if entities.get("rule"):
            scores[IntentType.GET_RULE] = scores.get(IntentType.GET_RULE, 0) + 40
        if entities.get("resource") and not entities.get("chapter"):
            scores[IntentType.GET_RESOURCE] = scores.get(IntentType.GET_RESOURCE, 0) + 30
        if entities.get("lo"):
            scores[IntentType.GET_LO] = scores.get(IntentType.GET_LO, 0) + 60
        if entities.get("chapter") and not entities.get("resource"):
            scores[IntentType.GET_TOPIC] = scores.get(IntentType.GET_TOPIC, 0) + 25
        if entities.get("assignment") or entities.get("part"):
            scores[IntentType.GET_ASSIGNMENT] = scores.get(IntentType.GET_ASSIGNMENT, 0) + 25

        if scores:
            best_intent = max(scores.items(), key=lambda item: item[1])
            if best_intent[1] > 0:
                return best_intent[0]

        return IntentType.UNKNOWN

    # ------------------------------------------------------------------
    # Entities
    # ------------------------------------------------------------------
    def extract_entities(
        self,
        text: str,
        intent: IntentType = IntentType.UNKNOWN,
    ) -> Dict[str, Any]:
        """
        Extract the entities of the query.

        The extraction is delegated to the lexicon, which resolves the
        overlaps by preferring the **longest** surface form.  On top of the
        lexicon result the analyzer adds the attribute of the question
        ("credits", "midterm_duration", ...) and the *scope* marker for the
        out-of-scope queries.
        """
        entities: Dict[str, Any] = {}

        # -- lexicon based extraction ------------------------------------
        matches = self.lexicon.lookup(
            text,
            priority_groups=[
                "assignment_part", "part_of_assignment", "assignment",
                "learning_outcome", "chapter", "week", "rule",
                "attribute", "topic", "course", "resource", "instructor",
            ],
        )

        for match in matches:
            key = match.entity_type
            if key in entities:
                # Keep the first (longest / highest priority) match.
                continue
            entities[key] = match.canonical

        # -- learning outcomes -------------------------------------------
        # The lexicon only knows the canonical identifiers; the query may
        # mention any of them, so a dedicated scan is still required.
        lo_match = re.search(r'\blo_(\d)(?:_(\d+))?', self.normalize_text(text))
        if lo_match:
            lo_main = lo_match.group(1)
            lo_sub = lo_match.group(2)
            lo_id = f"{lo_main}.{lo_sub}" if lo_sub else f"{lo_main}.1"
            entities['lo'] = f"LO{lo_id}"

        # -- explicit numbers ---------------------------------------------
        # The lexicon only lists the chapters and the weeks that really
        # exist.  A query that mentions a number outside that range
        # ("Chương 99 nói về gì?") still carries a *well formed* entity,
        # so the number is captured here and the knowledge base will
        # answer "not found" instead of the analyzer guessing a different
        # chapter.
        normalized = self.normalize_text(text)
        chapter_match = re.search(r'chương\s*(\d+)', normalized)
        if chapter_match:
            number = int(chapter_match.group(1))
            entities['chapter'] = f"CH{number:02d}"
        week_match = re.search(r'tuần\s*(\d+)', normalized)
        if week_match:
            number = int(week_match.group(1))
            entities['week'] = f"WEEK_{number:02d}"

        # -- out of scope -------------------------------------------------
        scope = self.lexicon.is_out_of_scope(text)
        if scope:
            entities['scope'] = 'OUT_OF_SCOPE'

        # -- attribute ----------------------------------------------------
        attribute = self._extract_attribute(text)
        if attribute:
            entities['attribute'] = attribute

        # -- assignment parts ---------------------------------------------
        if intent == IntentType.GET_ASSIGNMENT:
            if re.search(r"phần nào|những phần|phần nào của", self.normalize_text(text)):
                entities['list_parts'] = True
            # A question about the *files* that have to be delivered is
            # answered with the deliverable list of the part.
            if re.search(r"xuất file|file gì|file nào|output file|sinh file",
                         self.normalize_text(text)):
                entities['ask_deliverables'] = True

        return entities

    def _extract_attribute(self, text: str) -> Optional[str]:
        """Detect the attribute of the question about the course."""
        normalized = self.normalize_text(text)

        if re.search(r"giữa kỳ|midterm", normalized):
            return "midterm_duration"
        if re.search(r"cuối kỳ|\bfinal\b", normalized):
            return "final_duration"
        if re.search(r"tín chỉ|\bects\b", normalized):
            return "credits"
        if re.search(r"mục tiêu", normalized):
            return "learning_outcomes"
        if re.search(r"mô tả|giới thiệu", normalized):
            return "description"
        if re.search(r"bao nhiêu phút|kéo dài bao lâu|thời lượng", normalized):
            return "duration"
        if re.search(r"gồm những phần|phần chính|những phần nào|cấu trúc", normalized):
            return "parts"
        return None

    # ------------------------------------------------------------------
    # Full analysis
    # ------------------------------------------------------------------
    def analyze(
        self,
        text: str,
        tokens: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> SemanticRepresentation:
        """
        Perform the full semantic analysis.

        Args:
            text: the query.  When the pipeline has already resolved the
                contextual references, this is the *rewritten* query.
            tokens: the token list (optional, kept for backwards
                compatibility).
            context: the result of the dialogue resolution.  Two keys are
                understood:

                ``inferred_entities``
                    The entities that the discourse context suggests as the
                    referent of the query (e.g. the chapter that the pronoun
                    "nó" refers to).

                ``context_dependent``
                    ``True`` when the query contains a reference that has
                    *not* been resolved.  The intent then becomes
                    ``CONTEXT_DEPENDENT`` so that the pipeline asks for
                    clarification instead of guessing.
        """
        context = context or {}

        entities = self.extract_entities(text)
        intent = self.extract_intent(text, tokens, entities)

        # The entities that the dialogue manager could resolve are injected
        # *before* the intent is re-evaluated so that the referent of an
        # anaphor ("nó", "phần này") can influence the intent as well.
        resolved = {
            key: value
            for key, value in context.items()
            if key not in {"inferred_entities", "context_dependent", "unresolved_reference"}
        }
        for key, value in resolved.items():
            entities.setdefault(key, value)

        if resolved:
            intent = self.extract_intent(text, tokens, entities)

        # A query that cannot be resolved without the previous turn is
        # flagged as CONTEXT_DEPENDENT so that the pipeline asks for
        # clarification instead of guessing.
        if context.get("context_dependent"):
            intent = IntentType.CONTEXT_DEPENDENT

        # The entities that the dialogue manager could still infer are kept
        # so that the answer can mention the presumed referent.
        for key, value in (context.get("inferred_entities") or {}).items():
            entities.setdefault(key, value)

        sem_rep = SemanticRepresentation(
            intent=intent,
            entities=entities,
            raw_query=text,
        )
        return sem_rep

    def analyze_batch(self, texts: List[str]) -> List[SemanticRepresentation]:
        """Analyze multiple texts"""
        return [self.analyze(text) for text in texts]


# Example semantic representations
EXAMPLE_SEMANTIC_FORMS = {
    "Môn NLP có bao nhiêu tín chỉ?": "GET_COURSE_INFO(course=CO3085, attribute=credits)",
    "Tuần 3 học gì?": "GET_SCHEDULE(week=WEEK_03)",
    "Chương 4 nói về gì?": "GET_TOPIC(chapter=CH04)",
    "Chương nào học về CFG?": "GET_TOPIC(topic=CFG)",
    "Deadline BTL là khi nào?": "GET_DEADLINE(assignment=BTL01)",
    "Tài liệu về PCFG ở đâu?": "GET_RESOURCE(topic=PCFG)",
    "Có được sử dụng LLM không?": "GET_RULE(rule=LLM_RAG)",
    "L.O.4.2 là gì?": "GET_LO(lo=LO4.2)",
    "Nó có liên quan đến parsing không?": "CONTEXT_DEPENDENT()",
}


def main():
    """Test semantic analyzer"""
    analyzer = SemanticAnalyzer()

    test_queries = [
        "Môn NLP có bao nhiêu tín chỉ?",
        "Tuần 3 học gì?",
        "Chương 4 nói về gì?",
        "Chương nào học về CFG?",
        "Deadline BTL là khi nào?",
        "Tài liệu về PCFG ở đâu?",
        "Có được sử dụng LLM không?",
        "L.O.4.2 là gì?",
        "Midterm kéo dài bao lâu?",
    ]

    print("Semantic Analysis Results")
    print("=" * 70)

    for query in test_queries:
        sem_rep = analyzer.analyze(query)
        print(f"\nQuery: {query}")
        print(f"Intent: {sem_rep.intent.value}")
        print(f"Entities: {sem_rep.entities}")
        print(f"Logical Form: {sem_rep.to_logical_form()}")


if __name__ == "__main__":
    main()
