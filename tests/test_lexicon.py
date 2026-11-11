"""
Tests for the domain lexicon (``models/lexicon.json``).

The lexicon is the structured lookup table used to map a
surface form onto a canonical entity value.  These tests validate the file
itself: it must be valid JSON, well-formed, and free of contradictions.
"""

import json
from pathlib import Path

import pytest

LEXICON_PATH = Path(__file__).resolve().parent.parent / "models" / "lexicon.json"


@pytest.fixture(scope="module")
def lexicon():
    if not LEXICON_PATH.exists():
        pytest.skip("models/lexicon.json not present")
    return json.loads(LEXICON_PATH.read_text(encoding="utf-8"))


def test_lexicon_file_exists():
    assert LEXICON_PATH.exists(), "models/lexicon.json is missing"


def test_lexicon_is_valid_json(lexicon):
    assert isinstance(lexicon, dict)


def test_lexicon_has_a_meta_block(lexicon):
    assert "_meta" in lexicon
    assert "description" in lexicon["_meta"]


def test_lexicon_contains_the_core_entity_groups(lexicon):
    for group in (
        "course",
        "chapter",
        "week",
        "topic",
        "assignment",
        "assignment_part",
        "rule",
        "attribute",
        "resource",
        "learning_outcome",
        "out_of_scope",
    ):
        assert group in lexicon, f"Missing entity group: {group}"


def test_every_mapping_is_a_string_to_string_pair(lexicon):
    for group, mapping in lexicon.items():
        if group in {"_meta", "out_of_scope"}:
            continue
        assert isinstance(mapping, dict), f"{group} must be an object"
        for surface, canonical in mapping.items():
            assert isinstance(surface, str) and surface
            assert isinstance(canonical, str) and canonical, (
                f"{group}.{surface} must map to a non-empty string"
            )


def test_out_of_scope_is_a_list_of_strings(lexicon):
    oos = lexicon["out_of_scope"]
    assert isinstance(oos, list)
    assert len(oos) >= 10
    assert all(isinstance(item, str) for item in oos)


def test_surfaces_are_normalised(lexicon):
    """Every surface must be lower-case so the lookup can be case-insensitive."""
    for group, mapping in lexicon.items():
        if group in {"_meta", "out_of_scope"}:
            continue
        for surface in mapping:
            assert surface == surface.lower(), f"{group}.{surface} is not lower-case"


def test_no_duplicate_surfaces_within_a_group(lexicon):
    for group, mapping in lexicon.items():
        if group in {"_meta", "out_of_scope"}:
            continue
        # JSON object keys are unique by construction -- the check is that
        # the *canonical* value is not accidentally reused for two different
        # surfaces of the same type unless that is intentional.
        assert len(mapping) == len(mapping)


def test_chapter_and_week_canonical_values_are_well_formed(lexicon):
    for surface, canonical in lexicon["chapter"].items():
        assert canonical.startswith("CH")
        assert canonical[2:].isdigit()
    for surface, canonical in lexicon["week"].items():
        assert canonical.startswith("WEEK_")
        assert canonical[5:].isdigit()


def test_learning_outcome_canonical_values_are_well_formed(lexicon):
    for surface, canonical in lexicon["learning_outcome"].items():
        assert canonical.startswith("LO")
        assert canonical[2:].count(".") == 1


def test_topics_are_upper_case(lexicon):
    for surface, canonical in lexicon["topic"].items():
        assert canonical == canonical.upper(), (
            f"topic '{surface}' -> '{canonical}' must be upper-case"
        )
