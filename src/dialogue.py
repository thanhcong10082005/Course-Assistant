"""
Course Assistant - Dialogue Context Module
Handles local discourse context for multi-turn conversations
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum


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
    entities: Dict[str, DiscourseEntity] = field(default_factory=dict)
    history: List[Dict] = field(default_factory=list)


class DialogueManager:
    """
    Manages dialogue context and reference resolution
    Supports local discourse context for Course Assistant
    """
    
    def __init__(self):
        self.state = DialogueState()
        self.reference_patterns = self._build_reference_patterns()
    
    def _build_reference_patterns(self) -> Dict[str, List[str]]:
        """Build patterns for recognizing references"""
        return {
            "pronoun": ["nó", "hắn", "bạn", "tôi", "mình"],
            "demonstrative": ["này", "đó", "kia"],
            "definite_phrase": ["phần này", "phần đó", "chương này", "chương đó",
                              "bài này", "bài đó", "tuần này", "tuần đó"],
            "ellipsis": ["ở đâu", "là gì", "có không", "như thế nào"],
        }
    
    def reset(self):
        """Reset dialogue state"""
        self.state = DialogueState()
    
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
    
    def resolve_reference(self, query: str) -> Tuple[str, Dict[str, Any]]:
        """
        Resolve contextual references in query
        
        Args:
            query: User query that may contain references
            
        Returns:
            Tuple of (resolved_query, resolved_entities)
        """
        resolved_query = query
        resolved_entities = {}
        
        query_lower = query.lower()
        
        # Check for definite phrases
        for pattern in self.reference_patterns["definite_phrase"]:
            if pattern in query_lower:
                # Replace with actual reference
                if 'phần' in pattern:
                    if self.state.last_topic:
                        resolved_query = resolved_query.replace(pattern, self.state.last_topic)
                        resolved_entities['topic'] = self.state.last_topic
                    elif self.state.last_intent == 'GET_ASSIGNMENT':
                        resolved_query = resolved_query.replace(pattern, 'bài tập lớn')
                        resolved_entities['assignment'] = 'BTL01'
                
                elif 'chương' in pattern:
                    if self.state.last_chapter:
                        resolved_query = resolved_query.replace(pattern, self.state.last_chapter)
                        resolved_entities['chapter'] = self.state.last_chapter
                
                elif 'tuần' in pattern:
                    if self.state.last_week:
                        resolved_query = resolved_query.replace(pattern, self.state.last_week)
                        resolved_entities['week'] = self.state.last_week
        
        # Check for pronouns
        for pronoun in self.reference_patterns["pronoun"]:
            if pronoun in query_lower:
                # Try to resolve based on context
                if self.state.last_topic and 'topic' not in resolved_entities:
                    resolved_query = resolved_query.replace(pronoun, self.state.last_topic)
                    resolved_entities['topic'] = self.state.last_topic
        
        # Check for ellipsis patterns
        for pattern in self.reference_patterns["ellipsis"]:
            if pattern in query_lower:
                # This is an ellipsis - we need context
                if self.state.last_chapter:
                    resolved_entities['chapter'] = self.state.last_chapter
                elif self.state.last_topic:
                    resolved_entities['topic'] = self.state.last_topic
        
        return resolved_query, resolved_entities
    
    def get_state_summary(self) -> Dict:
        """Get a summary of current dialogue state"""
        return {
            'turn': self.state.turn,
            'last_intent': self.state.last_intent,
            'last_topic': self.state.last_topic,
            'last_chapter': self.state.last_chapter,
            'last_week': self.state.last_week,
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
