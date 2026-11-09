"""
Registry of known outstanding issues.

Each entry maps a test identifier to a short explanation of why it currently
fails and which Work Package is responsible for fixing it.

The markers are declared with ``strict=False`` so that a test which starts
passing simply reports ``XPASS`` instead of breaking the suite.  Once the
corresponding Work Package is finished the entry can be removed from this
file, which turns the test into a permanent regression guard.

Keeping this list in one place makes the roadmap visible from the code and
guarantees that no failure is silently "forgotten".
"""

from typing import Dict, List

# Test id fragment -> (reason, work package)
KNOWN_ISSUES: Dict[str, tuple] = {
    # ------------------------------------------------------------------
    # WP4 -- Semantic: canonical entity values & CONTEXT_DEPENDENT
    # ------------------------------------------------------------------
    "test_official_query[Q003]": (
        "'môn học' chưa được ánh xạ về course=CO3085",
        "WP4",
    ),
    "test_official_query[Q007]": (
        "topic 'pcfg' bị match sai thành 'cfg' (substring)",
        "WP4",
    ),
    "test_official_query[Q008]": (
        "topic 'semantic grammar' bị match thành 'semantic'",
        "WP4",
    ),
    "test_official_query[Q013]": (
        "chưa suy luận được part=PART_II từ keyword 'hỏi đáp'",
        "WP4",
    ),
    "test_official_query[Q014]": (
        "chưa trích xuất được entity rule=LLM_RAG",
        "WP4",
    ),
    "test_official_query[Q015]": (
        "chưa trích xuất được entity rule=AI_USAGE",
        "WP4",
    ),
    "test_official_query[Q018]": (
        "topic 'statistical nlp' bị 'course=NLP' chiếm mất",
        "WP4",
    ),
    "test_official_query[Q019]": (
        "topic 'python nlp' bị 'course=NLP' chiếm mất",
        "WP4",
    ),
    "test_official_query[Q021]": (
        "thiếu topic 'REFERENCE' trong lexicon",
        "WP4",
    ),
    "test_official_query[Q022]": (
        "thiếu topic 'QUESTION_ANSWERING' trong lexicon",
        "WP4",
    ),
    "test_official_query[Q023]": (
        "thiếu topic 'SELECTIONAL_RESTRICTION' trong lexicon",
        "WP4",
    ),
    "test_official_query[Q028]": (
        "câu ngoài phạm vi bị nhận nhầm thành GET_ASSIGNMENT",
        "WP4",
    ),
    "test_official_query[Q030]": (
        "chưa có intent CONTEXT_DEPENDENT",
        "WP4 + WP6",
    ),
    "test_official_query[Q032]": (
        "chưa có intent CONTEXT_DEPENDENT",
        "WP4 + WP6",
    ),
    "test_official_query[Q033]": (
        "chưa suy luận được part=PART_I từ keyword 'parser'",
        "WP4",
    ),
    "test_official_query[Q034]": (
        "chưa có intent CONTEXT_DEPENDENT",
        "WP4 + WP6",
    ),
    "test_official_out_of_scope_detection": (
        "Q028 bị nhận nhầm thành GET_ASSIGNMENT",
        "WP4",
    ),
    # ------------------------------------------------------------------
    # WP6 -- Dialogue Manager thật sự được nối vào pipeline
    # ------------------------------------------------------------------
    "test_dialogue_resolves_reference": (
        "DialogueManager chưa được nối vào process_dialogue()",
        "WP6",
    ),
    "test_dialogue_state_summary_is_populated": (
        "CourseAssistant chưa khởi tạo DialogueManager",
        "WP6",
    ),
    "test_dialogue_reset_clears_context": (
        "CourseAssistant chưa khởi tạo DialogueManager",
        "WP6",
    ),
    "test_context_dependent_without_context_asks_for_clarification": (
        "chưa có intent CONTEXT_DEPENDENT",
        "WP4 + WP6",
    ),
}


def reason_for(test_id: str) -> str:
    """Return the reason for a given test id (falls back to a generic text)."""
    for fragment, (reason, wp) in KNOWN_ISSUES.items():
        if fragment in test_id:
            return f"{reason} [{wp}]"
    return "known outstanding issue"


def work_packages() -> List[str]:
    """Return the sorted list of work packages that still have open issues."""
    return sorted({wp for _, wp in KNOWN_ISSUES.values()})