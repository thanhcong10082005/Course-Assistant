"""
CFG Grammar for Course Assistant Domain
Defines grammar rules for Vietnamese questions about course information
"""

from typing import List, Dict, Set, Tuple
import random


class GrammarRule:
    """Represents a CFG production rule"""
    
    def __init__(self, lhs: str, rhs: List[str]):
        self.lhs = lhs  # Left-hand side (non-terminal)
        self.rhs = rhs  # Right-hand side (terminals/non-terminals)
    
    def __repr__(self):
        return f"{self.lhs} -> {' '.join(self.rhs)}"
    
    def __str__(self):
        return self.__repr__()


class CFG:
    """
    Context-Free Grammar for Course Assistant
    Supports Vietnamese questions about NLP course
    """
    
    def __init__(self):
        self.rules: Dict[str, List[GrammarRule]] = {}
        self.terminals: Set[str] = set()
        self.nonterminals: Set[str] = set()
        self.start_symbol = "S"
        self._build_grammar()
    
    def _add_rule(self, lhs: str, rhs: List[str]):
        """Add a grammar rule"""
        rule = GrammarRule(lhs, rhs)
        if lhs not in self.rules:
            self.rules[lhs] = []
        self.rules[lhs].append(rule)
        self.nonterminals.add(lhs)
        for symbol in rhs:
            if symbol.islower() or symbol in {'?', '!'}:  # Terminal
                self.terminals.add(symbol)
            else:
                self.nonterminals.add(symbol)
    
    def _build_grammar(self):
        """Build the grammar for Course Assistant domain"""
        
        # Start symbol - sentence types
        self._add_rule("S", ["QUESTION"])
        self._add_rule("S", ["WH_QUESTION"])
        self._add_rule("S", ["YES_NO_QUESTION"])
        
        # Question types
        self._add_rule("QUESTION", ["WH_PHRASE", "NP", "VP", "?"])
        self._add_rule("WH_QUESTION", ["WH_WORD", "NP", "VP", "?"])
        self._add_rule("YES_NO_QUESTION", ["NP", "VP", "?"])
        
        # WH Words for course assistant
        self._add_rule("WH_WORD", ["môn"])
        self._add_rule("WH_WORD", ["tuần"])
        self._add_rule("WH_WORD", ["chương"])
        self._add_rule("WH_WORD", ["bài"])
        self._add_rule("WH_WORD", ["tài"])
        self._add_rule("WH_WORD", ["quy"])
        self._add_rule("WH_WORD", ["thời"])
        self._add_rule("WH_WORD", ["deadline"])
        self._add_rule("WH_WORD", ["ai"])
        self._add_rule("WH_WORD", ["ở"])
        self._add_rule("WH_WORD", ["đâu"])
        self._add_rule("WH_WORD", ["bao"])
        self._add_rule("WH_WORD", ["có"])
        self._add_rule("WH_WORD", ["là"])
        self._add_rule("WH_WORD", ["gì"])
        self._add_rule("WH_WORD", ["nào"])
        
        # Noun Phrases
        self._add_rule("NP", ["COURSE_NAME"])
        self._add_rule("NP", ["CHAPTER_NUM"])
        self._add_rule("NP", ["WEEK_NUM"])
        self._add_rule("NP", ["TOPIC_NAME"])
        self._add_rule("NP", ["ASSIGNMENT_NAME"])
        self._add_rule("NP", ["LO_ID"])
        self._add_rule("NP", ["PRONOUN"])
        self._add_rule("NP", ["DET", "NOMINAL"])
        self._add_rule("NP", ["DET"])
        self._add_rule("NP", ["NOMINAL"])
        
        # Nominal
        self._add_rule("NOMINAL", ["NOUN"])
        self._add_rule("NOMINAL", ["NOUN", "NOUN"])
        self._add_rule("NOMINAL", ["ADJ", "NOUN"])
        self._add_rule("NOMINAL", ["NOUN", "ADJ"])
        
        # Course names
        self._add_rule("COURSE_NAME", ["nlp"])
        self._add_rule("COURSE_NAME", ["co3085"])
        self._add_rule("COURSE_NAME", ["xử_lý_ngôn_ngữ_tự_nhiên"])
        
        # Chapter numbers
        for i in range(1, 13):
            self._add_rule("CHAPTER_NUM", [str(i)])
        
        # Week numbers
        for i in range(1, 16):
            self._add_rule("WEEK_NUM", [str(i)])
        
        # Topic names
        self._add_rule("TOPIC_NAME", ["cfg"])
        self._add_rule("TOPIC_NAME", ["pcfg"])
        self._add_rule("TOPIC_NAME", ["parsing"])
        self._add_rule("TOPIC_NAME", ["semantic"])
        self._add_rule("TOPIC_NAME", ["syntax"])
        self._add_rule("TOPIC_NAME", ["pos"])
        self._add_rule("TOPIC_NAME", ["feature"])
        self._add_rule("TOPIC_NAME", ["grammar"])
        
        # Assignment names
        self._add_rule("ASSIGNMENT_NAME", ["btl"])
        self._add_rule("ASSIGNMENT_NAME", ["bài_tập_lớn"])
        self._add_rule("ASSIGNMENT_NAME", ["assignment"])
        
        # Learning outcomes
        for i in range(1, 5):
            for j in range(1, 6):
                if i == 4 and j > 2:
                    break
                self._add_rule("LO_ID", [f"l.o.{i}.{j}"])
        
        # Pronouns
        self._add_rule("PRONOUN", ["tôi"])
        self._add_rule("PRONOUN", ["tớ"])
        self._add_rule("PRONOUN", ["mình"])
        self._add_rule("PRONOUN", ["nó"])
        self._add_rule("PRONOUN", ["phần_này"])
        self._add_rule("PRONOUN", ["chương_này"])
        
        # Determiners
        self._add_rule("DET", ["các"])
        self._add_rule("DET", ["những"])
        self._add_rule("DET", ["nào"])
        self._add_rule("DET", ["gì"])
        self._add_rule("DET", ["bao"])
        self._add_rule("DET", ["mấy"])
        self._add_rule("DET", ["này"])
        self._add_rule("DET", ["đó"])
        
        # Verbs
        self._add_rule("VERB", ["học"])
        self._add_rule("VERB", ["nói"])
        self._add_rule("VERB", ["có"])
        self._add_rule("VERB", ["xuất"])
        self._add_rule("VERB", ["liên_quan"])
        self._add_rule("VERB", ["ở"])
        self._add_rule("VERB", ["là"])
        self._add_rule("VERB", ["cần"])
        self._add_rule("VERB", ["muốn"])
        self._add_rule("VERB", ["biết"])
        self._add_rule("VERB", ["hỏi"])
        self._add_rule("VERB", ["tra"])
        self._add_rule("VERB", ["xem"])
        self._add_rule("VERB", ["tìm"])
        self._add_rule("VERB", ["yêu_cầu"])
        self._add_rule("VERB", ["sử_dụng"])
        self._add_rule("VERB", ["được"])
        
        # Nouns
        self._add_rule("NOUN", ["tín_chỉ"])
        self._add_rule("NOUN", ["môn_học"])
        self._add_rule("NOUN", ["chương"])
        self._add_rule("NOUN", ["tuần"])
        self._add_rule("NOUN", ["bài"])
        self._add_rule("NOUN", ["nội_dung"])
        self._add_rule("NOUN", ["tài_liệu"])
        self._add_rule("NOUN", ["quy_định"])
        self._add_rule("NOUN", ["deadline"])
        self._add_rule("NOUN", ["thời_hạn"])
        self._add_rule("NOUN", ["phần"])
        self._add_rule("NOUN", ["phần"])
        self._add_rule("NOUN", ["thông_tin"])
        self._add_rule("NOUN", ["yêu_cầu"])
        self._add_rule("NOUN", ["file"])
        self._add_rule("NOUN", ["output"])
        
        # Adjectives
        self._add_rule("ADJ", ["gì"])
        self._add_rule("ADJ", ["nào"])
        self._add_rule("ADJ", ["nào"])
        
        # Verb Phrases
        self._add_rule("VP", ["VERB"])
        self._add_rule("VP", ["VERB", "NP"])
        self._add_rule("VP", ["VERB", "PP"])
        self._add_rule("VP", ["VERB", "ADJ"])
        self._add_rule("VP", ["VERB", "ADV"])
        self._add_rule("VP", ["VERB", "NUM"])
        self._add_rule("VP", ["VERB", "ADJ", "NP"])
        self._add_rule("VP", ["VERB", "NUM", "NOUN"])
        
        # Prepositional Phrases
        self._add_rule("PP", ["PREP", "NP"])
        self._add_rule("PP", ["PREP", "NOUN"])
        
        # Prepositions
        self._add_rule("PREP", ["ở"])
        self._add_rule("PREP", ["về"])
        self._add_rule("PREP", ["của"])
        self._add_rule("PREP", ["với"])
        self._add_rule("PREP", ["cho"])
        
        # Adverbs
        self._add_rule("ADV", ["bao"])
        self._add_rule("ADV", ["nhiêu"])
        self._add_rule("ADV", ["không"])
        self._add_rule("ADV", ["có"])
        self._add_rule("ADV", ["được"])
        self._add_rule("ADV", ["gì"])
        
        # Numbers
        for num in ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', 
                    '11', '12', '13', '14', '15', '30', '60', '90']:
            self._add_rule("NUM", [num])
        
        # Special terminals
        self._add_rule("?", ["?"])
        self._add_rule("!", ["!"])
    
    def get_rules(self, lhs: str) -> List[GrammarRule]:
        """Get all rules for a given non-terminal"""
        return self.rules.get(lhs, [])
    
    def get_expansions(self, lhs: str) -> List[List[str]]:
        """Get all possible RHS expansions for a non-terminal"""
        return [rule.rhs for rule in self.get_rules(lhs)]
    
    def is_terminal(self, symbol: str) -> bool:
        """Check if symbol is a terminal"""
        return symbol in self.terminals or symbol in ['?', '!']
    
    def is_nonterminal(self, symbol: str) -> bool:
        """Check if symbol is a non-terminal"""
        return symbol in self.nonterminals
    
    def generate_sentence(self, symbol: str = None, max_depth: int = 20) -> str:
        """
        Generate a sentence from the grammar
        Uses recursive random expansion
        """
        if symbol is None:
            symbol = self.start_symbol
        
        rules = self.get_rules(symbol)
        if not rules:
            return symbol
        
        if max_depth <= 0:
            return symbol
        
        # Randomly select a rule
        rule = random.choice(rules)
        
        # Expand each symbol in RHS
        result = []
        for sym in rule.rhs:
            if self.is_terminal(sym):
                result.append(sym)
            else:
                result.append(self.generate_sentence(sym, max_depth - 1))
        
        return ' '.join(result)
    
    def generate_all_sentences(self, max_sentences: int = 10000, max_length: int = 15) -> List[str]:
        """Generate multiple sentences from the grammar"""
        sentences = set()
        attempts = 0
        max_attempts = max_sentences * 10
        
        while len(sentences) < max_sentences and attempts < max_attempts:
            sentence = self.generate_sentence()
            words = sentence.split()
            
            # Check length constraint
            if len(words) <= max_length:
                sentences.add(sentence)
            
            attempts += 1
        
        return sorted(list(sentences))
    
    def to_string(self) -> str:
        """Return grammar as string for output file"""
        lines = []
        for lhs in sorted(self.rules.keys()):
            rules = self.rules[lhs]
            for rule in rules:
                lines.append(str(rule))
        return '\n'.join(lines)
    
    def print_grammar(self):
        """Print grammar rules"""
        print("CFG Grammar for Course Assistant")
        print("=" * 50)
        for lhs in sorted(self.rules.keys()):
            print(f"\n{lhs}:")
            for rule in self.rules[lhs]:
                print(f"  -> {' '.join(rule.rhs)}")


# Sample templates for Course Assistant questions
COURSE_QUESTION_TEMPLATES = [
    # Course info questions
    ("Môn {course} có bao nhiêu tín chỉ?", "GET_COURSE_INFO"),
    ("{course} có mấy tín chỉ?", "GET_COURSE_INFO"),
    ("Môn học {course} gồm những phần nào?", "GET_COURSE_INFO"),
    ("{course} có những phần chính nào?", "GET_COURSE_INFO"),
    ("Mô tả môn {course}?", "GET_COURSE_INFO"),
    ("Mục tiêu của môn {course} là gì?", "GET_COURSE_INFO"),
    ("Midterm kéo dài bao lâu?", "GET_COURSE_INFO"),
    ("Final kéo dài bao lâu?", "GET_COURSE_INFO"),
    
    # Schedule questions
    ("Tuần {week} học những gì?", "GET_SCHEDULE"),
    ("Tuần {week} học gì?", "GET_SCHEDULE"),
    ("Hôm nay học gì?", "GET_SCHEDULE"),
    ("Chương {chapter} học vào tuần nào?", "GET_SCHEDULE"),
    ("{topic} được học ở tuần nào?", "GET_SCHEDULE"),
    
    # Topic questions
    ("Chương {chapter} nói về gì?", "GET_TOPIC"),
    ("Chương {chapter} có nội dung gì?", "GET_TOPIC"),
    ("Chương nào học về {topic}?", "GET_TOPIC"),
    ("{topic} nằm ở chương nào?", "GET_TOPIC"),
    ("Ai dạy môn {course}?", "GET_INSTRUCTOR"),
    
    # Assignment questions
    ("Bài tập lớn có những yêu cầu gì?", "GET_ASSIGNMENT"),
    ("Bài tập lớn gồm những phần nào?", "GET_ASSIGNMENT"),
    ("Phần {part} của BTL là gì?", "GET_ASSIGNMENT"),
    ("BTL cần xuất những file gì?", "GET_ASSIGNMENT"),
    
    # Deadline questions
    ("Deadline BTL là khi nào?", "GET_DEADLINE"),
    ("Thời hạn nộp bài tập lớn là bao giờ?", "GET_DEADLINE"),
    ("Khi nào cần nộp BTL?", "GET_DEADLINE"),
    
    # Resource questions
    ("Tài liệu về {topic} ở đâu?", "GET_RESOURCE"),
    ("Có tài liệu nào về {topic} không?", "GET_RESOURCE"),
    ("Sách tham khảo của môn học là gì?", "GET_RESOURCE"),
    ("Tài liệu nào liên quan đến {topic}?", "GET_RESOURCE"),
    
    # Rule questions
    ("Có được sử dụng LLM không?", "GET_RULE"),
    ("Quy định về sử dụng AI là gì?", "GET_RULE"),
    ("Được phép dùng thư viện nào?", "GET_RULE"),
    ("Quy định của môn học là gì?", "GET_RULE"),
    
    # Learning outcome questions
    ("L.O.{lo} là gì?", "GET_LO"),
    ("L.O.{lo} liên quan đến nội dung gì?", "GET_LO"),
]


def generate_template_sentences() -> List[Tuple[str, str]]:
    """Generate sentences from templates"""
    courses = ["NLP", "CO3085", "xử lý ngôn ngữ tự nhiên"]
    chapters = list(range(1, 13))
    weeks = list(range(1, 16))
    topics = ["CFG", "PCFG", "Parsing", "Semantic", "POS Tagging", "Feature"]
    parts = ["I", "II", "III", "IV"]
    los = ["1.1", "2.1", "2.5", "3.3", "4.1", "4.2"]
    
    sentences = []
    
    for template, intent in COURSE_QUESTION_TEMPLATES:
        try:
            # Replace placeholders with actual values
            sentence = template
            
            if "{course}" in sentence:
                for course in courses[:2]:  # Use first 2 courses
                    sentences.append((sentence.format(course=course), intent))
            elif "{chapter}" in sentence:
                for ch in chapters[:3]:  # Use first 3 chapters
                    sentences.append((sentence.format(chapter=ch), intent))
            elif "{week}" in sentence:
                for wk in weeks[:3]:  # Use first 3 weeks
                    sentences.append((sentence.format(week=wk), intent))
            elif "{topic}" in sentence:
                for topic in topics[:3]:  # Use first 3 topics
                    sentences.append((sentence.format(topic=topic), intent))
            elif "{part}" in sentence:
                for part in parts[:2]:  # Use first 2 parts
                    sentences.append((sentence.format(part=part), intent))
            elif "{lo}" in sentence:
                for lo in los[:3]:  # Use first 3 LOs
                    sentences.append((sentence.format(lo=lo), intent))
            else:
                sentences.append((sentence, intent))
        except:
            sentences.append((template, intent))
    
    return sentences


if __name__ == "__main__":
    # Test grammar
    grammar = CFG()
    grammar.print_grammar()
    
    print("\n" + "=" * 50)
    print("Generated sentences:")
    print("=" * 50)
    
    sentences = grammar.generate_all_sentences(max_sentences=20)
    for i, sent in enumerate(sentences[:20], 1):
        print(f"{i}. {sent}")
