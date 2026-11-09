"""
Official test-set regression tests.

Every case from ``tests/data/sample_queries.txt`` (34 queries) is asserted
against the system.  The tests are intentionally strict so that any future
refactor that silently degrades intent or entity extraction is caught
immediately.

The entity comparison uses an alias table because the official labels and the
internal canonical values differ for a handful of cases (e.g. the official
label ``MIDTERM`` corresponds to ``attribute=midterm_duration``).
"""

from typing import Dict

import pytest

from tests.conftest import load_official_cases


# ---------------------------------------------------------------------------
# Alias table: official label -> accepted internal entity values
# ---------------------------------------------------------------------------
ENTITY_ALIASES: Dict[str, Dict[str, list]] = {
    "CO3085": {"course": ["CO3085", "NLP"]},
    "MIDTERM": {"attribute": ["midterm_duration"]},
    "FINAL": {"attribute": ["final_duration"]},
    "OUT_OF_SCOPE": {"scope": ["OUT_OF_SCOPE"]},
}


def entity_matches(expected: str, entities: Dict) -> bool:
    """Check whether ``entities`` contains the expected value (alias-aware)."""
    if expected in ENTITY_ALIASES:
        spec = ENTITY_ALIASES[expected]
        for key, values in spec.items():
            if key == "scope":
                if entities.get("scope") in values:
                    return True
                continue
            if entities.get(key) in values:
                return True
        return False
    return expected in str(entities)


# ---------------------------------------------------------------------------
# Individual test cases (one pytest test per official query)
# ---------------------------------------------------------------------------
def _make_case_test(case):
    def _test(assistant):
        result = assistant.process_query(case["query"])

        assert result["intent"] == case["expected_intent"], (
            f"{case['id']} '{case['query']}': "
            f"expected intent {case['expected_intent']}, got {result['intent']}"
        )

        if case["expected_entity"]:
            assert entity_matches(case["expected_entity"], result["entities"]), (
                f"{case['id']} '{case['query']}': "
                f"expected entity {case['expected_entity']}, got {result['entities']}"
            )

    _test.__doc__ = f"{case['id']}: {case['query']}"
    return _test


OFFICIAL_CASES = load_official_cases()


@pytest.mark.parametrize("case", OFFICIAL_CASES, ids=[c["id"] for c in OFFICIAL_CASES])
def test_official_query(case, assistant):
    _make_case_test(case)(assistant)


# ---------------------------------------------------------------------------
# Aggregate metrics (used as a quick smoke signal)
# ---------------------------------------------------------------------------
def test_official_dataset_is_complete():
    """Guard against a corrupted / truncated copy of the sample data."""
    assert len(OFFICIAL_CASES) == 34, "Expected 34 official test cases"


def test_official_intent_accuracy_is_high(assistant):
    """Intent accuracy on the official set must not fall below the baseline."""
    correct = 0
    for case in OFFICIAL_CASES:
        if assistant.process_query(case["query"])["intent"] == case["expected_intent"]:
            correct += 1
    accuracy = correct / len(OFFICIAL_CASES) * 100
    assert accuracy >= 88.0, f"Intent accuracy dropped to {accuracy:.2f}%"


def test_official_out_of_scope_detection(assistant):
    """Out-of-scope queries must be classified as UNKNOWN."""
    oos = [c for c in OFFICIAL_CASES if c["is_out_of_scope"]]
    assert oos, "Sample data must contain out-of-scope cases"
    for case in oos:
        result = assistant.process_query(case["query"])
        assert result["intent"] == "UNKNOWN", (
            f"{case['id']} '{case['query']}' should be out-of-scope"
        )
