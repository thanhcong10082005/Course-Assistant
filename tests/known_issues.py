"""
Registry of known outstanding issues.

Each entry maps a test identifier to a short explanation of why it currently
fails.  The entries are used to mark the matching tests as ``xfail`` so that
the quality gate stays green while the defect is still open.

The markers are declared with ``strict=False`` so that a test which starts
passing simply reports ``XPASS`` instead of breaking the suite.  Once the
underlying defect is fixed the entry can be removed from this file, which
turns the test into a permanent regression guard.

Keeping this list in one place guarantees that no failure is silently
"forgotten".

Current status
--------------
All previously registered issues have been **resolved**.  The corresponding
entries have been removed from :data:`KNOWN_ISSUES`, so the affected tests
are now permanent regression guards and the whole suite is green
(``133 passed``).
"""

from typing import Dict, List

# Test id fragment -> (reason, area of the system)
KNOWN_ISSUES: Dict[str, tuple] = {
    # ------------------------------------------------------------------
    # No outstanding issue at the moment.
    #
    # The entries below are kept as *documentation* of the defects that have
    # already been fixed.  They are commented out on purpose: an entry in
    # this dictionary would mark the matching test as ``xfail`` and hide a
    # regression.
    # ------------------------------------------------------------------
    # "test_official_query[Q003]": ("'môn học' chưa được ánh xạ về course=CO3085", "semantic analysis"),
    # "test_official_query[Q007]": ("topic 'pcfg' bị match sai thành 'cfg' (substring)", "semantic analysis"),
    # "test_official_query[Q008]": ("topic 'semantic grammar' bị match thành 'semantic'", "semantic analysis"),
    # "test_official_query[Q013]": ("chưa suy luận được part=PART_II từ keyword 'hỏi đáp'", "semantic analysis"),
    # "test_official_query[Q014]": ("chưa trích xuất được entity rule=LLM_RAG", "semantic analysis"),
    # "test_official_query[Q015]": ("chưa trích xuất được entity rule=AI_USAGE", "semantic analysis"),
    # "test_official_query[Q018]": ("topic 'statistical nlp' bị 'course=NLP' chiếm mất", "semantic analysis"),
    # "test_official_query[Q019]": ("topic 'python nlp' bị 'course=NLP' chiếm mất", "semantic analysis"),
    # "test_official_query[Q021]": ("thiếu topic 'REFERENCE' trong lexicon", "lexicon"),
    # "test_official_query[Q022]": ("thiếu topic 'QUESTION_ANSWERING' trong lexicon", "lexicon"),
    # "test_official_query[Q023]": ("thiếu topic 'SELECTIONAL_RESTRICTION' trong lexicon", "lexicon"),
    # "test_official_query[Q028]": ("câu ngoài phạm vi bị nhận nhầm thành GET_ASSIGNMENT", "semantic analysis"),
    # "test_official_query[Q030]": ("chưa có intent CONTEXT_DEPENDENT", "semantic analysis + dialogue"),
    # "test_official_query[Q032]": ("chưa có intent CONTEXT_DEPENDENT", "semantic analysis + dialogue"),
    # "test_official_query[Q033]": ("chưa suy luận được part=PART_I từ keyword 'parser'", "semantic analysis"),
    # "test_official_query[Q034]": ("chưa có intent CONTEXT_DEPENDENT", "semantic analysis + dialogue"),
    # "test_official_out_of_scope_detection": ("Q028 bị nhận nhầm thành GET_ASSIGNMENT", "semantic analysis"),
    # "test_dialogue_resolves_reference": ("DialogueManager chưa được nối vào process_dialogue()", "dialogue manager"),
    # "test_dialogue_state_summary_is_populated": ("CourseAssistant chưa khởi tạo DialogueManager", "dialogue manager"),
    # "test_dialogue_reset_clears_context": ("CourseAssistant chưa khởi tạo DialogueManager", "dialogue manager"),
    # "test_context_dependent_without_context_asks_for_clarification": ("chưa có intent CONTEXT_DEPENDENT", "semantic analysis + dialogue"),
}


def reason_for(test_id: str) -> str:
    """Return the reason for a given test id (falls back to a generic text)."""
    for fragment, (reason, area) in KNOWN_ISSUES.items():
        if fragment in test_id:
            return f"{reason} [{area}]"
    return "known outstanding issue"


def affected_areas() -> List[str]:
    """Return the sorted list of system areas that still have open issues."""
    return sorted({area for _, area in KNOWN_ISSUES.values()})
