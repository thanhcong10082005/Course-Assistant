"""
Semantic Representation module for Course Assistant
Converts parsed sentences to semantic/logical forms
"""

import re
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


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


class SemanticAnalyzer:
    """
    Analyzes parsed sentences and converts them to semantic representations
    """
    
    def __init__(self):
        # Intent patterns - keywords associated with each intent
        self.intent_patterns = {
            IntentType.GET_COURSE_INFO: {
                'keywords': ['tín_chỉ', 'tín', 'chỉ', 'credit', 'phần', 'chính', 
                           'mô_tả', 'mục_tiêu', 'midterm', 'final', 'thi', 'thời_lượng',
                           'môn_học', 'học_phần', 'kểu', 'type', 'năm', 'học'],
                'patterns': [
                    r'(có|mấy|bao_nhiêu).*tín_chỉ',
                    r'gồm.*phần',
                    r'.*mô_tả.*',
                    r'.*mục_tiêu.*',
                    r'midterm.*',
                    r'final.*',
                ]
            },
            IntentType.GET_SCHEDULE: {
                'keywords': ['tuần', 'học', 'lịch', 'hôm_nay', 'ngày', 'thứ'],
                'patterns': [
                    r'tuần.*học',
                    r'học.*gì',
                    r'hôm_nay.*',
                ]
            },
            IntentType.GET_TOPIC: {
                'keywords': ['chương', 'nội_dung', 'topic', 'chapter', 'về', 
                           'nói', 'học_về', 'trình_bày', 'giới_thiệu'],
                'patterns': [
                    r'chương.*về',
                    r'chương.*nói',
                    r'chương.*nội_dung',
                    r'nói.*gì',
                    r'.*về.*',
                ]
            },
            IntentType.GET_ASSIGNMENT: {
                'keywords': ['bài_tập', 'btl', 'assignment', 'yêu_cầu', 'requirement',
                           'phần_i', 'phần_ii', 'part', 'xuất', 'file', 'output'],
                'patterns': [
                    r'bài_tập.*yêu_cầu',
                    r'btl.*gì',
                    r'phần.*btl',
                    r'.*yêu_cầu.*',
                ]
            },
            IntentType.GET_DEADLINE: {
                'keywords': ['deadline', 'thời_hạn', 'hạn_nộp', 'nộp', 'khi_nào', 
                           'bao_giờ', 'mấy_giờ', 'ngày', 'tháng'],
                'patterns': [
                    r'deadline.*',
                    r'.*thời_hạn.*',
                    r'.*hạn_nộp.*',
                    r'.*khi_nào.*',
                ]
            },
            IntentType.GET_RESOURCE: {
                'keywords': ['tài_liệu', 'tài_nguyên', 'sách', 'giáo_trình', 
                           'tham_khảo', 'resource', 'book', 'reference', 'đọc'],
                'patterns': [
                    r'tài_liệu.*',
                    r'.*sách.*',
                    r'.*tham_khảo.*',
                    r'.*resource.*',
                ]
            },
            IntentType.GET_RULE: {
                'keywords': ['quy_định', 'rule', 'regulation', 'được', 'phép', 
                           'không', 'được', 'sử_dụng', 'ai', 'policy'],
                'patterns': [
                    r'quy_định.*',
                    r'.*được.*phép.*',
                    r'.*không.*được.*',
                    r'.*sử_dụng.*',
                ]
            },
            IntentType.GET_INSTRUCTOR: {
                'keywords': ['ai', 'giảng', 'viên', 'dạy', 'thầy', 'cô', 'giáo'],
                'patterns': [
                    r'.*ai.*dạy.*',
                    r'.*giảng.*viên.*',
                ]
            },
            IntentType.GET_LO: {
                'keywords': ['l.o.', 'lo', 'learning', 'outcome', 'kết_quả', 'học_tập'],
                'patterns': [
                    r'l\.?o\.?\d+',
                    r'.*outcome.*',
                ]
            },
        }
    
    def normalize_text(self, text: str) -> str:
        """Normalize text for pattern matching"""
        # Lowercase and replace spaces with underscores
        text = text.lower().strip()
        # Preserve L.O.X.Y patterns: replace "l.o.X.Y" with "lo_X_Y"
        text = re.sub(r'l\.o\.(\d+)\.(\d+)', r'lo_\1_\2', text)
        # Replace "l.o.X" with "lo_X" (single level)
        text = re.sub(r'l\.o\.(\d+)(?!\.)', r'lo_\1', text)
        # Remove remaining punctuation
        text = text.replace('?', '').replace('.', '').replace(',', '')
        # Normalize spaces
        text = ' '.join(text.split())
        return text
    
    def extract_intent(self, text: str, tokens: List[str] = None) -> IntentType:
        """
        Extract intent from text using priority-based keyword matching and patterns
        Higher priority intents are checked first to resolve conflicts
        """
        normalized = self.normalize_text(text)
        tokens = tokens or normalized.split()
        
        # Priority order for intent detection
        # Check higher priority intents first to avoid conflicts
        priority_order = [
            IntentType.GET_DEADLINE,     # deadline/thời hạn is very specific
            IntentType.GET_LO,           # L.O.X.Y is very specific
            IntentType.GET_INSTRUCTOR,   # "ai dạy" is specific
            IntentType.GET_RULE,         # quy định is specific
            IntentType.GET_RESOURCE,     # tài liệu is specific
            IntentType.GET_ASSIGNMENT,   # bài tập lớn is specific
            IntentType.GET_SCHEDULE,     # tuần X is specific
            IntentType.GET_TOPIC,        # chương nào về X
            IntentType.GET_COURSE_INFO,  # general course info
        ]
        
        # First try to match with specific patterns
        import re
        
        # Out-of-scope detection first (queries unrelated to course)
        out_of_scope_patterns = [
            r'(thời tiết|mưa|nắng|nóng|lạnh)',
            r'(tổng thống|prime minister|chủ tịch nước|thủ tướng)',
            r'(bóng đá|thể thao|bơi|chạy)',
            r'(giá vàng|chứng khoán|bitcoin|crypto)',
            r'(bài toán|giải phương trình|tính tích phân)',
            r'(covid|dịch bệnh|vaccine)',
            r'(ai là|who is).*(tổng|thủ tướng|tổng_thống)',
        ]
        for pattern in out_of_scope_patterns:
            if re.search(pattern, normalized):
                return IntentType.UNKNOWN
        
        # Deadlines
        if re.search(r'(deadline|thời hạn|hạn nộp|nộp|khi nào nộp|bao giờ)', normalized):
            return IntentType.GET_DEADLINE
        
        # Learning Outcomes
        if re.search(r'lo_\d', normalized) or 'learning outcome' in normalized:
            return IntentType.GET_LO
        
        # Instructor
        if re.search(r'(ai dạy|giảng viên|ai giảng|thầy|cô giáo)', normalized):
            return IntentType.GET_INSTRUCTOR
        
        # Rules - require specific rule-related keywords
        if re.search(r'\b(quy định|được phép dùng|sử dụng llm|dùng llm|dùng ai|sử dụng ai|chính sách)\b', normalized):
            return IntentType.GET_RULE
        
        # Resources
        if re.search(r'(tài liệu|sách|giáo trình|tham khảo|resource)', normalized):
            return IntentType.GET_RESOURCE
        
        # Assignment
        if re.search(r'(bài tập lớn|btl|assignment)', normalized):
            return IntentType.GET_ASSIGNMENT
        
        # Schedule (only when week number present, or asking about which week)
        if re.search(r'tuần\s*\d+', normalized):
            return IntentType.GET_SCHEDULE
        if re.search(r'(lịch học|kế hoạch học)', normalized):
            return IntentType.GET_SCHEDULE
        # "Chương X học vào tuần nào?" - asking about which week a chapter is taught
        if re.search(r'(chương|ch).*tuần nào', normalized):
            return IntentType.GET_SCHEDULE
        # Topic learning "ở tuần nào"
        if re.search(r'(học|dạy).*(ở|vào)\s*tuần nào', normalized):
            return IntentType.GET_SCHEDULE
        
        # Topic - chapter nói về / chương nào nói / chương X nói
        if re.search(r'(chương nào|chương \d+|nói về|nội dung gì)', normalized):
            return IntentType.GET_TOPIC
        # Topic patterns like "X học ở đâu" (asking which chapter teaches topic)
        if re.search(r'(cfg|pcfg|parsing|semantic|grammar|syntax|feature|dependency|knowledge|discourse|reference)\s+(được\s+)?(học|dạy|trình bày)', normalized):
            return IntentType.GET_TOPIC
        
        # Score each intent
        scores = {}
        for intent, config in self.intent_patterns.items():
            score = 0
            for keyword in config['keywords']:
                keyword_normalized = keyword.replace('_', ' ')
                if keyword_normalized in normalized or keyword in tokens:
                    score += 1
            for pattern in config.get('patterns', []):
                if re.search(pattern, normalized):
                    score += 2
            scores[intent] = score
        
        # Get intent with highest score
        if scores:
            best_intent = max(scores.items(), key=lambda x: x[1])
            if best_intent[1] > 0:
                return best_intent[0]
        
        return IntentType.UNKNOWN
    
    def extract_entities(self, text: str, intent: IntentType) -> Dict[str, Any]:
        """
        Extract entities based on intent
        """
        normalized = self.normalize_text(text)
        entities = {}
        tokens = normalized.split()
        
        # Course name
        if 'nlp' in tokens or 'co3085' in tokens:
            entities['course'] = 'CO3085' if 'co3085' in tokens else 'NLP'
        
        # Chapter number
        import re
        chapter_match = re.search(r'chương\s*(\d+)', normalized)
        if chapter_match:
            entities['chapter'] = f"CH{chapter_match.group(1).zfill(2)}"
        
        # Week number
        week_match = re.search(r'tuần\s*(\d+)', normalized)
        if week_match:
            entities['week'] = f"WEEK_{week_match.group(1).zfill(2)}"
        
        # Topic names
        topic_keywords = {
            'cfg': 'CFG', 'pcfg': 'PCFG', 'parsing': 'PARSING', 
            'semantic': 'SEMANTIC', 'syntax': 'SYNTAX', 'pos': 'POS',
            'feature': 'FEATURE', 'grammar': 'GRAMMAR', 'tagging': 'TAGGING',
            'disambiguation': 'WSD', 'dependency': 'DEPENDENCY'
        }
        for keyword, topic in topic_keywords.items():
            if keyword in normalized:
                entities['topic'] = topic
                break
        
        # Assignment
        if 'btl' in tokens or 'bài_tập_lớn' in normalized or 'bài tập lớn' in normalized:
            entities['assignment'] = 'BTL01'
        
        # Assignment part (Part I, Part II, etc.)
        # Match patterns like "Phần I", "Part I", "phần nào" (when asking about parts)
        if intent == IntentType.GET_ASSIGNMENT:
            part_match = re.search(r'phần\s*(i{1,3}|iv|v|\d+)', normalized)
            if part_match:
                part_roman = part_match.group(1).upper()
                roman_to_num = {'I': 'I', 'II': 'II', 'III': 'III', 'IV': 'IV', 'V': 'V'}
                if part_roman in roman_to_num:
                    entities['part'] = f"PART_{roman_to_num[part_roman]}"
            # If asking about which parts (gồm những phần nào), mark for full listing
            if 'phần nào' in normalized or 'những phần' in normalized:
                entities['list_parts'] = True
        
        # Learning Outcome - match lo_X or lo_X_Y where X is single digit
        lo_match = re.search(r'lo_(\d)(?:_(\d+))?', normalized)
        if lo_match:
            lo_main = lo_match.group(1)
            lo_sub = lo_match.group(2)
            if lo_sub:
                lo_id = f"{lo_main}.{lo_sub}"
            else:
                lo_id = f"{lo_main}.1"  # Default to .1 if no sub specified
            entities['lo'] = f"LO{lo_id}"
        
        # Specific attributes based on intent
        if IntentType.GET_COURSE_INFO in [intent]:
            if 'tín' in normalized or 'credit' in normalized or 'mấy tín' in normalized:
                entities['attribute'] = 'credits'
            elif 'midterm' in normalized or 'giữa_kỳ' in normalized or 'giữa kỳ' in normalized:
                entities['attribute'] = 'midterm_duration'
            elif 'final' in normalized or 'cuối_kỳ' in normalized or 'cuối kỳ' in normalized:
                entities['attribute'] = 'final_duration'
            elif re.search(r'phần|chính|gồm những', normalized):
                entities['attribute'] = 'parts'
            elif 'mô tả' in normalized or 'giới thiệu' in normalized:
                entities['attribute'] = 'description'
            elif 'mục tiêu' in normalized or 'outcome' in normalized:
                entities['attribute'] = 'learning_outcomes'
        
        return entities
    
    def analyze(self, text: str, tokens: List[str] = None) -> SemanticRepresentation:
        """
        Perform full semantic analysis
        """
        # Extract intent
        intent = self.extract_intent(text, tokens)
        
        # Extract entities
        entities = self.extract_entities(text, intent)
        
        # Create semantic representation
        sem_rep = SemanticRepresentation(
            intent=intent,
            entities=entities,
            raw_query=text
        )
        
        return sem_rep
    
    def analyze_batch(self, texts: List[str]) -> List[SemanticRepresentation]:
        """Analyze multiple texts"""
        return [self.analyze(text) for text in texts]


# Example semantic representations
EXAMPLE_SEMANTIC_FORMS = {
    "Môn NLP có bao nhiêu tín chỉ?": "GET_COURSE_INFO(course=NLP, attribute=credits)",
    "Tuần 3 học gì?": "GET_SCHEDULE(week=WEEK_03)",
    "Chương 4 nói về gì?": "GET_TOPIC(chapter=CH04)",
    "Chương nào học về CFG?": "GET_TOPIC(topic=CFG)",
    "Deadline BTL là khi nào?": "GET_DEADLINE(assignment=BTL01)",
    "Tài liệu về PCFG ở đâu?": "GET_RESOURCE(topic=PCFG)",
    "Có được sử dụng LLM không?": "GET_RULE(rule=LLM_USAGE)",
    "L.O.4.2 là gì?": "GET_LO(lo=LO4.2)",
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
