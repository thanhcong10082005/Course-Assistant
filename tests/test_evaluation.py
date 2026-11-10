"""
Tests for the evaluation framework.

The framework is the measurement instrument of the project, so it deserves
its own tests: a wrong measurement would silently make the whole report
unreliable.  These tests therefore check

1. that the test suite is **complete** (all three sources, the expected
   number of cases),
2. that the metric computation is correct (accuracy, per intent, per
   category),
3. that the entity comparison is **alias aware** (the official label
   ``MIDTERM`` must match the extracted ``midterm_duration``),
4. that the rendered report contains the **six sections** the assignment
   asks for, and
5. that the accuracy does **not** drop below the agreed thresholds -- this
   is the regression guard of the whole project.
"""

import os
from typing import Dict, List

import pytest

from src.evaluation import (
    CATEGORY_CONTEXT,
    CATEGORY_IN_SCOPE,
    CATEGORY_KB_MISS,
    CATEGORY_OUT_OF_SCOPE,
    ENTITY_ALIASES,
    EvaluationReport,
    EvaluationResult,
    Evaluator,
    build_test_suite,
    entity_matches,
    load_dialogue_cases,
    load_official_cases,
    load_paraphrase_cases,
    render_report,
)
from src.evaluation import TestCase as EvalTestCase

# The thresholds the project has to keep.
MIN_INTENT_ACCURACY = 95.0
MIN_ENTITY_ACCURACY = 90.0


# ---------------------------------------------------------------------------
# The test suite itself
# ---------------------------------------------------------------------------
def test_official_cases_are_loaded():
    """The 34 official queries are read from the file."""
    cases = load_official_cases()
    assert len(cases) == 34, "the official test set has 34 cases"
    assert cases[0].case_id == "Q001"
    assert cases[0].source == "official"


def test_official_cases_skip_headers_and_comments():
    """The section headers of the file are not mistaken for test cases."""
    cases = load_official_cases()
    for case in cases:
        assert case.case_id.startswith("Q")
        assert "|" not in case.query
        assert "-----" not in case.query


def test_paraphrase_cases_are_loaded():
    """The paraphrased cases cover every category the assignment lists."""
    cases = load_paraphrase_cases()
    assert len(cases) == 15
    categories = {case.category for case in cases}
    assert CATEGORY_OUT_OF_SCOPE in categories
    assert CATEGORY_KB_MISS in categories


def test_dialogue_cases_are_loaded():
    """The multi-turn cases carry the questions that build the context."""
    cases = load_dialogue_cases()
    assert len(cases) == 8
    for case in cases:
        if case.context_setup:
            assert case.category == CATEGORY_CONTEXT


def test_full_test_suite_has_the_expected_size():
    """The three sources are combined into one suite."""
    suite = build_test_suite()
    assert len(suite) == 57
    sources = {case.source for case in suite}
    assert sources == {"official", "paraphrase", "dialogue"}


def test_test_suite_has_no_duplicate_queries():
    """
    Two cases with the same question would hide a labelling error.

    The only legitimate overlap is between the *official* context-dependent
    questions (asked on their own) and the *dialogue* questions (asked with
    a discourse context): the very same sentence has a different expected
    outcome in the two situations, and that difference is exactly what the
    evaluation has to demonstrate.
    """
    suite = build_test_suite()
    seen: Dict[str, List] = {}
    for case in suite:
        seen.setdefault(case.query, []).append(case)

    for query, cases in seen.items():
        if len(cases) == 1:
            continue
        sources = {case.source for case in cases}
        categories = {case.category for case in cases}
        assert sources == {"official", "dialogue"}, (
            f"unexpected duplicate of {query!r}: {sources}"
        )
        # The official case has no context, the dialogue case has one.
        assert all(not case.context_setup for case in cases if case.source == "official")
        assert all(case.context_setup for case in cases if case.source == "dialogue")
        assert categories == {CATEGORY_CONTEXT}


# ---------------------------------------------------------------------------
# The alias table
# ---------------------------------------------------------------------------
def test_alias_table_accepts_the_canonical_value():
    """A label that matches the extracted value is accepted."""
    assert entity_matches("CO3085", {"course": "CO3085"})
    assert entity_matches("CH04", {"chapter": "CH04"})


def test_alias_table_accepts_an_alias():
    """The official label may differ from the canonical value."""
    assert entity_matches("CO3085", {"course": "NLP"})
    assert entity_matches("MIDTERM", {"attribute": "midterm_duration"})
    assert entity_matches("FINAL", {"attribute": "final_duration"})


def test_alias_table_rejects_a_wrong_value():
    """A wrong entity must not be accepted."""
    assert not entity_matches("CO3085", {"course": "OTHER"})
    assert not entity_matches("CH04", {"chapter": "CH05"})


def test_empty_expectation_is_always_satisfied():
    """A case without an expected entity only checks the intent."""
    assert entity_matches(None, {})
    assert entity_matches("", {"chapter": "CH01"})


def test_out_of_scope_alias_is_checked_through_the_scope_entity():
    """The out-of-scope label is matched through the ``scope`` entity."""
    assert entity_matches("OUT_OF_SCOPE", {"scope": "OUT_OF_SCOPE"})
    assert not entity_matches("OUT_OF_SCOPE", {"scope": "IN_SCOPE"})


def test_alias_table_only_refers_to_known_entity_keys():
    """Every alias must point at an entity key the pipeline produces."""
    known = {"course", "chapter", "week", "topic", "assignment", "part",
             "rule", "attribute", "resource", "lo", "instructor", "scope"}
    for spec in ENTITY_ALIASES.values():
        for key in spec:
            assert key in known or key == "__scope__"


# ---------------------------------------------------------------------------
# The metric computation
# ---------------------------------------------------------------------------
def _result(case, intent_correct=True, entity_correct=True, error_type=None):
    return EvaluationResult(
        test_case=case,
        predicted_intent=case.expected_intent if intent_correct else "WRONG",
        predicted_entities={},
        intent_correct=intent_correct,
        entity_correct=entity_correct,
        error_type=error_type,
    )


def test_accuracy_properties():
    """The accuracies are computed from the counters."""
    case = EvalTestCase(query="q", expected_intent="GET_TOPIC")
    report = EvaluationReport(
        total_tests=2,
        intent_correct=2,
        entity_correct=1,
        results=[_result(case), _result(case, entity_correct=False)],
    )
    assert report.intent_accuracy == 100.0
    assert report.entity_accuracy == 50.0
    assert report.combined_accuracy == 50.0


def test_accuracy_of_an_empty_report_is_zero():
    """An empty report must not divide by zero."""
    report = EvaluationReport()
    assert report.intent_accuracy == 0
    assert report.entity_accuracy == 0
    assert report.combined_accuracy == 0


def test_per_intent_and_per_category():
    """The breakdowns group the results correctly."""
    case_a = EvalTestCase(query="a", expected_intent="GET_TOPIC")
    case_b = EvalTestCase(query="b", expected_intent="GET_RULE")
    report = EvaluationReport(
        total_tests=2,
        results=[_result(case_a), _result(case_b, intent_correct=False,
                                          error_type="intent_error")],
    )
    per_intent = report.per_intent()
    assert per_intent["GET_TOPIC"] == (1, 1)
    assert per_intent["GET_RULE"] == (0, 1)
    assert report.error_distribution() == {"intent_error": 1}


def test_error_distribution_counts_only_the_failures():
    """A passing case does not appear in the error distribution."""
    case = EvalTestCase(query="q", expected_intent="GET_TOPIC")
    report = EvaluationReport(
        total_tests=2,
        results=[_result(case), _result(case, intent_correct=False,
                                        error_type="intent_error")],
    )
    assert report.error_distribution() == {"intent_error": 1}


# ---------------------------------------------------------------------------
# The evaluation of the real system
# ---------------------------------------------------------------------------
@pytest.fixture(scope="module")
def evaluation_report():
    """The report of the system on the complete test suite."""
    from src.main import CourseAssistant

    evaluator = Evaluator(CourseAssistant())
    evaluator.load_test_cases(build_test_suite())
    return evaluator.evaluate()


def test_intent_accuracy_meets_the_threshold(evaluation_report):
    """The intent accuracy must not drop below the agreed threshold."""
    assert evaluation_report.intent_accuracy >= MIN_INTENT_ACCURACY, (
        evaluation_report.error_distribution()
    )


def test_entity_accuracy_meets_the_threshold(evaluation_report):
    """The entity accuracy must not drop below the agreed threshold."""
    assert evaluation_report.entity_accuracy >= MIN_ENTITY_ACCURACY, (
        evaluation_report.error_distribution()
    )


def test_out_of_scope_detection_is_perfect(evaluation_report):
    """Every out-of-scope question is detected."""
    assert evaluation_report.out_of_scope_accuracy == 100.0


def test_every_intent_of_the_test_set_is_covered(evaluation_report):
    """The report has an accuracy figure for every intent."""
    per_intent = evaluation_report.per_intent()
    for intent in (
        "GET_COURSE_INFO", "GET_SCHEDULE", "GET_TOPIC", "GET_ASSIGNMENT",
        "GET_DEADLINE", "GET_RESOURCE", "GET_RULE", "GET_INSTRUCTOR",
        "GET_LO", "CONTEXT_DEPENDENT", "UNKNOWN",
    ):
        assert intent in per_intent, f"missing the intent {intent}"


def test_the_multi_turn_cases_really_use_the_context():
    """
    The dialogue cases must not pass by accident.

    Without the discourse context the question "Nó có liên quan đến parsing
    không?" cannot be answered at all -- the system would have to guess the
    chapter.  The test therefore verifies that the *same* question asked
    without a context yields a different (unresolved) answer.
    """
    from src.main import CourseAssistant

    assistant = CourseAssistant()
    assistant.process_dialogue("Chương 4 nói về gì?")
    with_context, context = assistant.process_dialogue(
        "Nó có liên quan đến parsing không?"
    )
    assert context.get("entities", {}).get("chapter") == "CH04"

    lonely = CourseAssistant()
    alone = lonely.process_query("Nó có liên quan đến parsing không?")
    assert alone["intent"] == "CONTEXT_DEPENDENT"


# ---------------------------------------------------------------------------
# The rendered report
# ---------------------------------------------------------------------------
def test_report_has_the_six_required_sections(evaluation_report):
    """The report contains the six sections the assignment asks for."""
    from src.evaluation import build_full_report

    text = build_full_report()
    for section in (
        "1. SỐ LƯỢNG CÂU KIỂM THỬ",
        "2. SỐ LƯỢNG CÂU TRẢ LỜI ĐÚNG",
        "3. ĐỘ CHÍNH XÁC THEO TỪNG INTENT",
        "4. CÁC TRƯỜNG HỢP HỆ THỐNG TRẢ LỜI SAI",
        "5. PHÂN TÍCH NGUYÊN NHÂN LỖI",
        "6. NHẬN XÉT ƯU ĐIỂM VÀ HẠN CHẾ",
    ):
        assert section in text, f"missing the section {section}"


def test_report_states_the_number_of_cases(evaluation_report):
    """The report mentions the size of every source."""
    from src.evaluation import build_full_report

    text = build_full_report()
    assert "57 câu" in text
    assert "34 câu" in text
    assert "15 câu" in text
    assert "8 câu" in text


def test_report_of_an_empty_evaluation_is_handled():
    """Rendering without a report does not crash."""
    evaluator = Evaluator()
    assert "No evaluation results" in evaluator.generate_report()


def test_render_report_uses_the_supplied_cases():
    """The rendering does not depend on a global state."""
    case = EvalTestCase(query="q", expected_intent="GET_TOPIC")
    report = EvaluationReport(total_tests=1, intent_correct=1, results=[_result(case)])
    text = render_report(report, [case])
    assert "GET_TOPIC" in text
    assert "1 câu" in text
