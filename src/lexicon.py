"""
Domain lexicon for the Course Assistant.

The lexicon is the **single source of truth** for mapping a *surface form*
(the way a user writes something) onto a *canonical value* (the way the
knowledge base stores it).  It replaces the ad-hoc keyword dictionaries that
used to live inside :mod:`src.semantic`.

Design notes
------------
* **Longest match wins.**  ``"semantic grammar"`` must beat ``"semantic"`` and
  ``"statistical nlp"`` must beat ``"nlp"``.  The matcher therefore collects
  every candidate surface and resolves the overlaps by preferring the longest
  one, which removes the whole class of "substring steals the entity" bugs.
* **Group priority.**  Some surfaces belong to more than one group
  (``"hỏi đáp"`` is both a topic and a part of the assignment).  The caller
  can pass a priority list so that the semantically relevant group wins.
* **Group → entity key.**  Each group is mapped onto the entity key used by
  the semantic representation (``topic``, ``part``, ``lo``, ...).

The file itself lives in ``models/lexicon.json`` and is validated by
``tests/test_lexicon.py``.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Set, Tuple

DEFAULT_LEXICON_PATH = (
    Path(__file__).resolve().parent.parent / "models" / "lexicon.json"
)


# ---------------------------------------------------------------------------
# Group -> semantic entity key
# ---------------------------------------------------------------------------
GROUP_TO_ENTITY_KEY: Dict[str, str] = {
    "course": "course",
    "chapter": "chapter",
    "week": "week",
    "topic": "topic",
    "assignment": "assignment",
    "assignment_part": "part",
    "part_of_assignment": "part",
    "rule": "rule",
    "attribute": "attribute",
    "resource": "resource",
    "learning_outcome": "lo",
    "instructor": "instructor",
}

# The order in which entity keys are applied when several groups could
# produce the same key.  Earlier wins.
ENTITY_KEY_PRIORITY: List[str] = [
    "course",
    "chapter",
    "week",
    "topic",
    "assignment",
    "part",
    "rule",
    "attribute",
    "resource",
    "lo",
    "instructor",
]

# Groups that describe an *out of scope* request.
OUT_OF_SCOPE_GROUP = "out_of_scope"

# Group that lists the contextual references.
CONTEXT_REFERENCE_GROUP = "context_reference"


@dataclass(frozen=True)
class LexiconMatch:
    """A single surface form found in the text."""

    entity_type: str
    surface: str
    canonical: str
    start: int
    end: int
    group: str

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        return (
            f"LexiconMatch({self.entity_type}={self.canonical!r} "
            f"from {self.surface!r} @[{self.start}:{self.end}])"
        )


class Lexicon:
    """
    Lookup table ``surface form -> canonical value`` for the course domain.

    The lexicon is loaded once and cached; matching is performed on the
    lower-cased text so that the lookup is case insensitive.
    """

    def __init__(self, path: Optional[Path] = None) -> None:
        self.path = Path(path) if path else DEFAULT_LEXICON_PATH
        self._data: Dict = {}
        self._group_patterns: Dict[str, re.Pattern] = {}
        self._reference_patterns: Dict[str, re.Pattern] = {}
        self._out_of_scope_patterns: List[re.Pattern] = []
        self._load()

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------
    def _load(self) -> None:
        if not self.path.exists():
            raise FileNotFoundError(f"Lexicon file not found: {self.path}")
        self._data = json.loads(self.path.read_text(encoding="utf-8"))

        groups = {
            name: mapping
            for name, mapping in self._data.items()
            if name not in {"_meta", OUT_OF_SCOPE_GROUP, CONTEXT_REFERENCE_GROUP}
            and isinstance(mapping, dict)
        }
        self.groups: Dict[str, Dict[str, str]] = groups

        for name, mapping in groups.items():
            if not mapping:
                continue
            self._group_patterns[name] = self._compile(list(mapping.keys()))

        self.out_of_scope: List[str] = list(
            self._data.get(OUT_OF_SCOPE_GROUP, [])
        )
        self._out_of_scope_patterns = [
            self._compile([surface]) for surface in self.out_of_scope
        ]

        references = self._data.get(CONTEXT_REFERENCE_GROUP, {})
        self.context_reference: Dict[str, str] = dict(references)
        self._reference_patterns = {
            surface: self._compile([surface]) for surface in references
        }

    @staticmethod
    def _compile(surfaces: Sequence[str]) -> re.Pattern:
        """
        Build a regex that matches any of the given surfaces.

        The surfaces are matched longest-first so that the alternation itself
        already prefers the longest surface at a given position.
        """
        alternatives = sorted(
            (surface for surface in surfaces if surface),
            key=lambda s: (-len(s), s),
        )
        if not alternatives:
            return re.compile(r"(?!x)x")  # never matches
        escaped = [
            re.escape(surface).replace(r"\ ", r"\s+").replace("_", r"[_\s]")
            for surface in alternatives
        ]
        return re.compile("|".join(escaped))

    # ------------------------------------------------------------------
    # Matching
    # ------------------------------------------------------------------
    def lookup(
        self,
        text: str,
        groups: Optional[Iterable[str]] = None,
        exclude_groups: Optional[Iterable[str]] = None,
        priority_groups: Optional[Iterable[str]] = None,
    ) -> List[LexiconMatch]:
        """
        Find every lexicon surface inside ``text``.

        Overlapping matches are resolved by preferring the **longest** match;
        ties are broken by the order of ``priority_groups`` and finally by the
        position of the match.
        """
        if not text:
            return []

        lowered = text.lower()
        wanted: Optional[Set[str]] = set(groups) if groups is not None else None
        excluded: Set[str] = set(exclude_groups or ())
        priority = list(priority_groups or ())

        candidates: List[LexiconMatch] = []
        for name, mapping in self.groups.items():
            if name in excluded:
                continue
            if wanted is not None and name not in wanted:
                continue
            pattern = self._group_patterns.get(name)
            if pattern is None:
                continue
            for match in pattern.finditer(lowered):
                surface = match.group(0)
                canonical = mapping.get(surface)
                if canonical is None:
                    # The matched text may differ in spacing from the key.
                    canonical = mapping.get(surface.replace(" ", "_"))
                if canonical is None:
                    canonical = mapping.get(surface.replace("_", " "))
                if canonical is None:
                    continue
                candidates.append(
                    LexiconMatch(
                        entity_type=GROUP_TO_ENTITY_KEY.get(name, name),
                        surface=surface,
                        canonical=canonical,
                        start=match.start(),
                        end=match.end(),
                        group=name,
                    )
                )

        if not candidates:
            return []

        def sort_key(match: LexiconMatch) -> Tuple:
            try:
                priority_index = priority.index(match.group)
            except ValueError:
                priority_index = len(priority)
            # longest first, then group priority, then position
            return (-(match.end - match.start), priority_index, match.start)

        candidates.sort(key=sort_key)

        selected: List[LexiconMatch] = []
        for candidate in candidates:
            overlaps = any(
                not (candidate.end <= other.start or candidate.start >= other.end)
                for other in selected
            )
            if overlaps:
                continue
            selected.append(candidate)

        selected.sort(key=lambda m: m.start)
        return selected

    def entities_for(
        self,
        text: str,
        groups: Optional[Iterable[str]] = None,
        exclude_groups: Optional[Iterable[str]] = None,
        priority_groups: Optional[Iterable[str]] = None,
    ) -> Dict[str, str]:
        """
        Return ``{entity_key: canonical_value}`` for the surfaces found.

        When several groups map onto the same entity key the first one (in
        text order) wins, except for the keys listed in
        :data:`ENTITY_KEY_PRIORITY` where the highest priority group wins.
        """
        matches = self.lookup(
            text,
            groups=groups,
            exclude_groups=exclude_groups,
            priority_groups=priority_groups,
        )

        entities: Dict[str, str] = {}
        owners: Dict[str, str] = {}

        def rank(entity_type: str) -> int:
            try:
                return ENTITY_KEY_PRIORITY.index(entity_type)
            except ValueError:
                return len(ENTITY_KEY_PRIORITY)

        for match in matches:
            key = match.entity_type
            if key not in entities:
                entities[key] = match.canonical
                owners[key] = match.group
            elif rank(key) < rank(owners.get(key, key)):
                entities[key] = match.canonical
                owners[key] = match.group

        return entities

    # ------------------------------------------------------------------
    # Special groups
    # ------------------------------------------------------------------
    def is_out_of_scope(self, text: str) -> Optional[str]:
        """Return the out-of-scope surface found in ``text`` (or ``None``)."""
        if not text:
            return None
        lowered = text.lower()
        for surface, pattern in zip(self.out_of_scope, self._out_of_scope_patterns):
            if pattern.search(lowered):
                return surface
        return None

    def find_reference(self, text: str) -> Optional[LexiconMatch]:
        """
        Return the contextual reference contained in ``text`` (or ``None``).

        Longer references are preferred so that ``"phần này"`` wins over the
        pronoun ``"nó"``.
        """
        if not text:
            return None
        lowered = text.lower()
        found: List[LexiconMatch] = []
        for surface, pattern in self._reference_patterns.items():
            match = pattern.search(lowered)
            if match:
                found.append(
                    LexiconMatch(
                        entity_type="reference",
                        surface=surface,
                        canonical=self.context_reference.get(surface, surface),
                        start=match.start(),
                        end=match.end(),
                        group=CONTEXT_REFERENCE_GROUP,
                    )
                )
        if not found:
            return None
        found.sort(key=lambda m: (-(m.end - m.start), m.start))
        return found[0]

    def has_reference(self, text: str) -> bool:
        """True when ``text`` contains a contextual reference."""
        return self.find_reference(text) is not None

    # ------------------------------------------------------------------
    # Introspection helpers
    # ------------------------------------------------------------------
    @property
    def meta(self) -> Dict:
        return self._data.get("_meta", {})

    def surface_count(self) -> int:
        """Total number of surface forms in the lexicon."""
        return sum(len(mapping) for mapping in self.groups.values())

    def __repr__(self) -> str:  # pragma: no cover - debugging helper
        return (
            f"Lexicon(path={self.path.name!r}, groups={len(self.groups)}, "
            f"surfaces={self.surface_count()})"
        )


# ---------------------------------------------------------------------------
# Module level helpers
# ---------------------------------------------------------------------------
_DEFAULT_LEXICON: Optional[Lexicon] = None


def get_lexicon(path: Optional[Path] = None) -> Lexicon:
    """Return the shared lexicon instance (loaded once)."""
    global _DEFAULT_LEXICON
    if path is not None:
        return Lexicon(path)
    if _DEFAULT_LEXICON is None:
        _DEFAULT_LEXICON = Lexicon()
    return _DEFAULT_LEXICON
