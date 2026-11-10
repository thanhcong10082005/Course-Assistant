"""
Course Assistant - Dialogue Context Module
Handles local discourse context for multi-turn conversations

Discourse context
----------------
The reference resolution is not a bag of ``str.replace`` calls: it is driven by
a proper **discourse state** (turn counter, last intent, last
topic / chapter / week / part / learning outcome and a table of discourse
entities) that is shared with the rest of the system.

The module implemented here

* resolves the four classical reference types -- **pronoun**, **demonstrative**,
  **definite description** and **ellipsis** -- against that state,
* understands the "next" relation ("chương sau") which needs the domain
  knowledge of the course (12 chapters, 15 weeks),
* reports whether the reference could be resolved at all, so that the
  pipeline can answer with a request for clarification instead of an
  invented answer, and
* remembers the turns it has already interpreted, which lets the pipeline
  answer a repeated question consistently.
"""

from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import re


class ReferenceType(Enum):
    """Types of contextual references"""
    PRONOUN = "pronoun"           # nó, hắn, cô ấy
    DEMONSTRATIVE = "demonstrative"  # này, đó, kia
    DEFINITE = "definite"         # cái đó, phần này
    ELLIPSIS = "ellipsis"         # (implied)
    TOPIC_CONTINUATION = "topic"  # "phần này", "chương này"


@dataclass
class DiscourseEntity:
    """Represents a discourse entity in context"""
    entity_type: str
    value: str
    mention: str  # How it was mentioned
    introduced_at: int  # Turn number
    last_mentioned_at: int  # Turn number
    salience: float = 1.0  # Importance score


@dataclass
class DialogueState:
    """Current state of dialogue"""
    turn: int = 0
    last_intent: str = ""
    last_topic: Optional[str] = None
    last_chapter: Optional[str] = None
    last_week: Optional[str] = None
    last_part: Optional[str] = None
    last_assignment: Optional[str] = None
    last_lo: Optional[str] = None
    entities: Dict[str, DiscourseEntity] = field(default_factory=dict)
    history: List[Dict] = field(default_factory=list)
    # Turns that have already been interpreted: raw query -> interpretation.
    resolved_turns: Dict[str, Dict[str, Any]] = field(default_factory=dict)


class DialogueManager:
    """
    Manages dialogue context and reference resolution
    Supports local discourse context for Course Assistant
    """

    # The maximum number of chapters / weeks of the course.  Needed to
    # resolve the "next" relation ("Còn chương sau?").
    MAX_CHAPTER = 12
    MAX_WEEK = 15

    def __init__(self, schedule: Optional[Dict[str, Dict[str, Any]]] = None):
        self.state = DialogueState()
        self.reference_patterns = self._build_reference_patterns()
        # The weekly schedule is needed to infer the chapter of a week
        # ("Tuần 3 học gì?" -> "chương này" -> chapter 3).
        self.schedule = schedule or {}

    def _build_reference_patterns(self) -> Dict[str, List[str]]:
        """Build patterns for recognizing references"""
        return {
            "pronoun": ["nó", "hắn", "chúng"],
            "demonstrative": ["này", "đó", "kia"],
            "definite_phrase": ["nội dung này", "phần này", "phần đó",
                              "chương này", "chương đó", "bài này", "bài đó",
                              "tuần này", "tuần đó", "đề này", "cái này"],
            "ellipsis": ["ở đâu", "là gì", "có không", "như thế nào",
                         "học gì", "nói về gì"],
            "next": ["chương sau", "tuần sau", "phần sau", "tiếp theo"],
        }

    def reset(self):
        """Reset dialogue state"""
        self.state = DialogueState()

    # ------------------------------------------------------------------
    # Session state
    # ------------------------------------------------------------------
    @property
    def has_active_session(self) -> bool:
        """
        ``True`` when an explicit multi-turn dialogue is running.

        The flag distinguishes two situations:

        * a **live session** -- the user is talking to the assistant and the
          previous turns are available, so a reference can be *resolved*;
        * a **standalone query** -- the question is asked on its own, so a
          reference can only be *reported* (``CONTEXT_DEPENDENT``) together
          with the most likely referent.
        """
        return self.state.turn > 0

    # ------------------------------------------------------------------
    # Context update
    # ------------------------------------------------------------------
    def note_context(self, entities: Dict[str, Any], query: str = "") -> None:
        """
        Remember the entities of a turn **without** opening a session.

        The standalone entry point (:meth:`src.main.CourseAssistant.process_query`)
        uses this method so that the assistant still knows *what has been
        discussed* -- and can therefore suggest the most likely referent of
        a contextual reference -- while the question itself stays
        context-dependent.
        """
        if not entities:
            return

        for key, state_key in (
            ("topic", "last_topic"),
            ("chapter", "last_chapter"),
            ("week", "last_week"),
            ("part", "last_part"),
            ("assignment", "last_assignment"),
            ("lo", "last_lo"),
        ):
            if key in entities:
                setattr(self.state, state_key, entities[key])
                self._add_entity(key, entities[key], query)

    def update_context(self, intent: str, entities: Dict[str, Any], query: str):
        """
        Update dialogue context with new information

        Args:
            intent: Intent of current turn
            entities: Extracted entities
            query: Original query
        """
        self.state.turn += 1
        self.state.last_intent = intent

        # Update topic/chapter/week if present
        if 'topic' in entities:
            self.state.last_topic = entities['topic']
            self._add_entity('topic', entities['topic'], query)

        if 'chapter' in entities:
            self.state.last_chapter = entities['chapter']
            self._add_entity('chapter', entities['chapter'], query)

        if 'week' in entities:
            self.state.last_week = entities['week']
            self._add_entity('week', entities['week'], query)

        if 'part' in entities:
            self.state.last_part = entities['part']
            self._add_entity('part', entities['part'], query)

        if 'assignment' in entities:
            self.state.last_assignment = entities['assignment']
            self._add_entity('assignment', entities['assignment'], query)

        if 'lo' in entities:
            self.state.last_lo = entities['lo']
            self._add_entity('lo', entities['lo'], query)

        # Add to history
        self.state.history.append({
            'turn': self.state.turn,
            'intent': intent,
            'entities': entities,
            'query': query
        })

    def _add_entity(self, entity_type: str, value: str, mention: str):
        """Add an entity to the discourse context"""
        entity = DiscourseEntity(
            entity_type=entity_type,
            value=value,
            mention=mention,
            introduced_at=self.state.turn,
            last_mentioned_at=self.state.turn,
            salience=1.0
        )
        self.state.entities[entity_type] = entity

    # ------------------------------------------------------------------
    # Reference detection
    # ------------------------------------------------------------------
    def has_reference(self, query: str) -> bool:
        """True when the query contains a contextual reference."""
        lowered = (query or "").lower()
        if self._contains_pronoun(lowered):
            return True
        for pattern in self.reference_patterns["definite_phrase"]:
            if self._contains_definite_phrase(lowered, pattern):
                return True
        for pattern in self.reference_patterns["next"]:
            if pattern in lowered:
                return True
        if self._is_ellipsis(lowered):
            return True
        return False

    @staticmethod
    def _contains_definite_phrase(lowered: str, pattern: str) -> bool:
        """
        True when ``lowered`` contains the definite phrase ``pattern``.

        The phrase must be a **complete** word sequence and it must not be
        part of a longer noun phrase.  Without the second condition the
        phrase ``"phần này"`` would be found inside ``"học phần này"``
        ("this course module"), which is a *self-contained* question about
        the course and not a reference to the previous turn.
        """
        for match in re.finditer(re.escape(pattern), lowered):
            # The adjacent characters must not continue the word.
            if match.start() > 0 and lowered[match.start() - 1].isalnum():
                continue
            if match.end() < len(lowered) and lowered[match.end()].isalnum():
                continue

            # The word in front of the phrase must not turn it into a
            # compound noun ("học phần này" = "this course module").
            prefix = lowered[:match.start()].rstrip()
            if prefix.endswith("học"):
                continue

            return True
        return False

    # ------------------------------------------------------------------
    # Reference resolution
    # ------------------------------------------------------------------
    def resolve_reference(self, query: str) -> Tuple[str, Dict[str, Any]]:
        """
        Resolve the contextual references of a query.

        Returns:
            Tuple of ``(resolved_query, resolved_entities)``.

            The resolved entities carry two extra keys:

            ``unresolved_reference``
                ``True`` when the query *contains* a reference but nothing
                in the discourse state could resolve it.  The pipeline then
                answers with a request for clarification.

            ``inferred_entities``
                The entities that were assumed from the context (used to
                enrich the answer).
        """
        resolved_query = query
        resolved_entities: Dict[str, Any] = {}
        inferred: Dict[str, Any] = {}

        query_lower = (query or "").lower()
        has_reference = False

        # -- "next" references ("Còn chương sau?") ----------------------
        # These change the *meaning* of the noun phrase, so the query is
        # rewritten ("chương sau" -> "chương 12").  The rewritten query then
        # yields the chapter / week entity on its own.
        for pattern in self.reference_patterns["next"]:
            if pattern not in query_lower:
                continue
            has_reference = True
            next_chapter = self._next_chapter()
            next_week = self._next_week()
            if 'chương' in pattern and next_chapter:
                resolved_query = self._replace_ci(resolved_query, pattern, f"chương {next_chapter}")
                resolved_entities['chapter'] = f"CH{next_chapter:02d}"
                inferred['chapter'] = f"CH{next_chapter:02d}"
            elif 'tuần' in pattern and next_week:
                resolved_query = self._replace_ci(resolved_query, pattern, f"tuần {next_week}")
                resolved_entities['week'] = f"WEEK_{next_week:02d}"
                inferred['week'] = f"WEEK_{next_week:02d}"
            elif next_chapter:
                resolved_query = self._replace_ci(resolved_query, pattern, f"chương {next_chapter}")
                resolved_entities['chapter'] = f"CH{next_chapter:02d}"
                inferred['chapter'] = f"CH{next_chapter:02d}"
            break

        # -- definite descriptions ("phần này", "chương này") -----------
        # These are *anaphoric*: the referent is known from the discourse
        # state.  The query is therefore left untouched and the referent is
        # injected as an entity -- rewriting the sentence would add spurious
        # surface forms ("chương 3") that would change the intent.
        for pattern in sorted(self.reference_patterns["definite_phrase"], key=len, reverse=True):
            if not self._contains_definite_phrase(query_lower, pattern):
                continue
            has_reference = True

            if pattern.startswith("nội dung"):
                # "Nội dung này" refers to the learning outcome or the topic
                # that was discussed last.
                if self.state.last_lo:
                    resolved_entities['lo'] = self.state.last_lo
                    inferred['lo'] = self.state.last_lo
                elif self.state.last_topic:
                    resolved_entities['topic'] = self.state.last_topic
                    inferred['topic'] = self.state.last_topic

            elif pattern.startswith("phần"):
                if self.state.last_part:
                    resolved_entities['part'] = self.state.last_part
                    inferred['part'] = self.state.last_part
                elif self.state.last_topic:
                    resolved_entities['topic'] = self.state.last_topic
                    inferred['topic'] = self.state.last_topic
                elif self.state.last_assignment:
                    resolved_entities['assignment'] = self.state.last_assignment
                    inferred['assignment'] = self.state.last_assignment
                elif self.state.last_intent == 'GET_ASSIGNMENT':
                    resolved_entities['assignment'] = 'BTL01'
                    inferred['assignment'] = 'BTL01'

            elif pattern.startswith("chương"):
                chapter = self.state.last_chapter or self._chapter_of_week()
                if chapter:
                    resolved_entities['chapter'] = chapter
                    inferred['chapter'] = chapter
                elif self.state.last_topic:
                    resolved_entities['topic'] = self.state.last_topic
                    inferred['topic'] = self.state.last_topic

            elif pattern.startswith("tuần"):
                if self.state.last_week:
                    resolved_entities['week'] = self.state.last_week
                    inferred['week'] = self.state.last_week

            elif pattern.startswith("bài") or pattern.startswith("đề"):
                if self.state.last_assignment:
                    resolved_entities['assignment'] = self.state.last_assignment
                    inferred['assignment'] = self.state.last_assignment

        # -- pronouns ("nó") ---------------------------------------------
        # The pronoun refers to the most salient discourse entity.  A
        # chapter is preferred over a topic because a question like
        # "Chương 4 nói về gì?" / "Nó có liên quan đến parsing không?"
        # continues the *chapter* thread.
        if self._contains_pronoun(query_lower):
            has_reference = True
            if self.state.last_chapter:
                resolved_entities['chapter'] = self.state.last_chapter
                inferred['chapter'] = self.state.last_chapter
            elif self.state.last_topic:
                resolved_entities['topic'] = self.state.last_topic
                inferred['topic'] = self.state.last_topic
            elif self.state.last_week:
                resolved_entities['week'] = self.state.last_week
                inferred['week'] = self.state.last_week

        # -- ellipsis ("Vậy thì ...?") -----------------------------------
        if self._is_ellipsis(query_lower):
            has_reference = True
            if self.state.last_chapter:
                resolved_entities.setdefault('chapter', self.state.last_chapter)
                inferred.setdefault('chapter', self.state.last_chapter)
            elif self.state.last_topic:
                resolved_entities.setdefault('topic', self.state.last_topic)
                inferred.setdefault('topic', self.state.last_topic)
            elif self.state.last_week:
                resolved_entities.setdefault('week', self.state.last_week)

        if inferred:
            resolved_entities['inferred_entities'] = inferred

        if has_reference and not resolved_entities:
            resolved_entities['unresolved_reference'] = True

        return resolved_query, resolved_entities

    # ------------------------------------------------------------------
    # Remembered turns
    # ------------------------------------------------------------------
    def remember_turn(self, query: str, intent: str, entities: Dict[str, Any]) -> None:
        """Store the interpretation of a turn so that it can be replayed."""
        self.state.resolved_turns[query] = {
            'intent': intent,
            'entities': dict(entities),
        }

    def recall_turn(self, query: str) -> Optional[Dict[str, Any]]:
        """The stored interpretation of a turn (``None`` when unknown)."""
        return self.state.resolved_turns.get(query)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _contains_pronoun(query_lower: str) -> bool:
        """True when the query contains a third-person pronoun."""
        for pronoun in ("nó", "hắn", "chúng"):
            if re.search(rf"(?<!\w){pronoun}(?!\w)", query_lower):
                return True
        return False

    @staticmethod
    def _replace_pronoun(query: str, replacement: str) -> str:
        """Replace the pronoun "nó" (and friends) by ``replacement``."""
        return re.sub(
            r"(?<!\w)(nó|hắn|chúng)(?!\w)", replacement, query, flags=re.IGNORECASE
        )

    @staticmethod
    def _replace_ci(query: str, pattern: str, replacement: str) -> str:
        """
        Replace ``pattern`` by ``replacement`` ignoring the case.

        The reference patterns are stored in lower case ("phần này") but the
        user may write "Phần này" -- a plain ``str.replace`` would then leave
        the reference untouched.
        """
        return re.sub(re.escape(pattern), replacement, query, flags=re.IGNORECASE)

    def _is_ellipsis(self, query_lower: str) -> bool:
        """True when the query has no subject of its own."""
        # A query that names a chapter / week / topic explicitly is not an
        # ellipsis even though it contains a question word.
        if any(marker in query_lower for marker in ("chương", "tuần", "bài tập lớn")):
            # "còn chương sau?" is an ellipsis of the chapter thread.
            return "chương sau" in query_lower or "tuần sau" in query_lower

        starters = ("còn", "vậy", "rồi", "thế", "nó", "nữa")
        return any(query_lower.startswith(word) for word in starters)

    def _next_chapter(self) -> Optional[int]:
        """The number of the chapter that follows the current one."""
        if not self.state.last_chapter:
            return None
        try:
            current = int(self.state.last_chapter.replace('CH', ''))
        except ValueError:
            return None
        if current < self.MAX_CHAPTER:
            return current + 1
        return None

    def _next_week(self) -> Optional[int]:
        """The number of the week that follows the current one."""
        if not self.state.last_week:
            return None
        try:
            current = int(self.state.last_week.replace('WEEK_', ''))
        except ValueError:
            return None
        if current < self.MAX_WEEK:
            return current + 1
        return None

    def _chapter_of_week(self) -> Optional[str]:
        """The chapter that is taught in the current week."""
        if not self.state.last_week or not self.schedule:
            return None
        info = self.schedule.get(self.state.last_week)
        if not info:
            return None
        return info.get("chapter")

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------
    def get_state_summary(self) -> Dict:
        """Get a summary of current dialogue state"""
        return {
            'turn': self.state.turn,
            'last_intent': self.state.last_intent,
            'last_topic': self.state.last_topic,
            'last_chapter': self.state.last_chapter,
            'last_week': self.state.last_week,
            'last_part': self.state.last_part,
            'last_assignment': self.state.last_assignment,
            'last_lo': self.state.last_lo,
            'entity_count': len(self.state.entities)
        }

    def get_history(self, limit: int = 5) -> List[Dict]:
        """Get recent dialogue history"""
        return self.state.history[-limit:]


# Example dialogue processing
EXAMPLE_DIALOGUES = [
    {
        "dialogue_id": "DIALOGUE_01",
        "turns": [
            {"user": "Tuần 3 học gì?", "expected_intent": "GET_SCHEDULE"},
            {"user": "Tài liệu của phần này ở đâu?", "expected_intent": "GET_RESOURCE",
             "expected_reference": "phần này -> WEEK_03 content"},
        ]
    },
    {
        "dialogue_id": "DIALOGUE_02",
        "turns": [
            {"user": "Chương 4 nói về gì?", "expected_intent": "GET_TOPIC"},
            {"user": "Nó có liên quan đến parsing không?", "expected_intent": "GET_TOPIC",
             "expected_reference": "Nó -> CH04"},
        ]
    },
]


def demo_dialogue():
    """Demonstrate dialogue processing"""
    manager = DialogueManager()

    print("Dialogue Context Demo")
    print("=" * 60)

    # First turn
    print("\n[Turn 1]")
    query1 = "Tuần 3 học gì?"
    print(f"User: {query1}")

    entities1 = {"week": "WEEK_03", "topic": "CFG, Parsing"}
    manager.update_context("GET_SCHEDULE", entities1, query1)

    print(f"Intent: GET_SCHEDULE")
    print(f"Entities: {entities1}")
    print(f"State: {manager.get_state_summary()}")

    # Second turn with reference
    print("\n[Turn 2]")
    query2 = "Tài liệu của phần này ở đâu?"
    print(f"User: {query2}")

    resolved_query, resolved_entities = manager.resolve_reference(query2)
    print(f"Resolved Query: {resolved_query}")
    print(f"Resolved Entities: {resolved_entities}")

    # Update context
    manager.update_context("GET_RESOURCE", resolved_entities, query2)
    print(f"State: {manager.get_state_summary()}")


if __name__ == "__main__":
    demo_dialogue()
