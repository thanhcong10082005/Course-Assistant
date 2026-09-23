"""
Parser module for Course Assistant
Implements recursive descent parser for CFG grammar
"""

from typing import List, Dict, Tuple, Optional, Set
from dataclasses import dataclass, field
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from .grammar import CFG
from .preprocessing import Preprocessor


@dataclass
class ParseNode:
    """Represents a node in the parse tree"""
    symbol: str
    children: List['ParseNode'] = field(default_factory=list)
    word: str = ""
    
    def __repr__(self):
        if self.children:
            return f"({self.symbol} {' '.join(str(c) for c in self.children)})"
        return f"({self.symbol} {self.word})" if self.word else f"({self.symbol})"
    
    def to_tree_string(self, indent: int = 0, prefix: str = "") -> str:
        """Convert parse tree to formatted string"""
        lines = []
        if self.children:
            for i, child in enumerate(self.children):
                is_last = i == len(self.children) - 1
                new_prefix = prefix + ("└── " if is_last else "├── ")
                lines.append(f"{new_prefix}{child.symbol}: {child.word}" if child.word else f"{new_prefix}{child.symbol}")
                if child.children:
                    extension = "    " if is_last else "│   "
                    lines.extend(child.to_tree_string(indent + 1, prefix + extension).split('\n'))
        return '\n'.join(lines)


class Parser:
    """
    Recursive Descent Parser for Course Assistant CFG
    Supports parsing Vietnamese questions about NLP course
    """
    
    def __init__(self, grammar: CFG = None):
        self.grammar = grammar if grammar else CFG()
        self.preprocessor = Preprocessor()
        self.tokens: List[Tuple[str, str]] = []
        self.pos_tags: List[Tuple[str, str]] = []
        self.current_pos: int = 0
        self.errors: List[str] = []
        
        # Build lookup tables for terminals
        self._build_lookup_tables()
    
    def _build_lookup_tables(self):
        """Build lookup tables for terminals"""
        self.wh_words = {'môn', 'tuần', 'chương', 'bài', 'tài', 'quy', 'thời', 
                        'deadline', 'ai', 'ở', 'đâu', 'bao', 'có', 'là', 'gì', 'nào',
                        'các', 'những', 'học', 'nói', 'có', 'xuất', 'liên', 'quan',
                        'cần', 'muốn', 'biết', 'hỏi', 'tra', 'xem', 'tìm', 'yêu', 
                        'cầu', 'sử', 'dụng', 'được', 'nộp'}
        
        self.course_names = {'nlp', 'co3085', 'xử_lý_ngôn_ngữ_tự_nhiên', 'xử', 'lí'}
        self.numbers = {str(i) for i in range(1, 100)}
        self.topics = {'cfg', 'pcfg', 'parsing', 'semantic', 'syntax', 'pos', 
                      'feature', 'grammar', 'tagging', 'disambiguation'}
        self.assignment_names = {'btl', 'bài_tập_lớn', 'assignment', 'bài', 'tập', 'lớn'}
        
        # POS tag mappings
        self.pos_to_category = {
            'NOUN': 'NP', 'PRONOUN': 'NP', 'COURSE_NAME': 'NP',
            'CHAPTER_NUM': 'NP', 'WEEK_NUM': 'NP', 'TOPIC_NAME': 'NP',
            'ASSIGNMENT_NAME': 'NP', 'LO_ID': 'NP', 'NUM': 'NP', 'DET': 'NP',
            'VERB': 'VP', 'ADJ': 'VP', 'ADV': 'VP', 'PREP': 'PP',
            'WH_WORD': 'WH_WORD', '?': '?', '!': '!'
        }
    
    def tokenize_input(self, text: str) -> List[Tuple[str, str]]:
        """Tokenize and POS tag input text"""
        preprocessed = self.preprocessor.preprocess(text)
        tokens = preprocessed['tokens']
        pos_tags = [(t, self.preprocessor.get_token_pos(t)) for t in tokens]
        return pos_tags
    
    def parse(self, text: str) -> Tuple[Optional[ParseNode], List[str]]:
        """
        Parse input text using recursive descent
        Returns: (parse_tree, errors)
        """
        self.tokens = self.tokenize_input(text)
        self.current_pos = 0
        self.errors = []
        
        if not self.tokens:
            return None, ["Empty input"]
        
        # Try to parse as a question
        tree = self._parse_question()
        
        if tree and self.current_pos == len(self.tokens):
            return tree, []
        
        # Fallback: use pattern-based parsing if recursive descent failed
        fallback_tree = self._parse_fallback(text)
        if fallback_tree:
            return fallback_tree, []
        
        self.errors.append(f"Parse incomplete at position {self.current_pos}/{len(self.tokens)}")
        return None, self.errors
    
    def _parse_fallback(self, text: str) -> Optional[ParseNode]:
        """
        Fallback pattern-based parser for sentences that don't fit 
        the strict CFG. Builds a tree by recognizing common patterns.
        """
        import re
        
        # Build flat list of (token, category) pairs
        tokens_info = []
        for token, pos in self.tokens:
            token_lower = token.lower()
            
            if token in ['?', '!']:
                category = 'PUNCT'
            elif token_lower in self.course_names:
                category = 'COURSE_NAME'
            elif token_lower in self.numbers:
                category = 'NUM'
            elif token_lower in self.topics:
                category = 'TOPIC'
            elif token_lower in self.assignment_names:
                category = 'ASSIGNMENT'
            elif token_lower.startswith('l.o.') or token_lower.startswith('l_o_') or re.match(r'^l\.?o\.?\d', token_lower) or re.match(r'^lo_\d', token_lower):
                category = 'LO_ID'
            elif token_lower in {'môn', 'tuần', 'chương', 'bài', 'tài', 'quy', 'thời', 'deadline'}:
                category = 'WH_WORD'
            elif token_lower in {'học', 'nói', 'có', 'xuất', 'liên', 'quan', 'cần', 'muốn', 'biết', 'hỏi', 'tra', 'xem', 'tìm', 'yêu', 'cầu', 'sử', 'dụng', 'được', 'nộp', 'kéo', 'dài', 'là', 'ở', 'về', 'của', 'với', 'cho', 'gồm'}:
                category = 'VERB'
            elif token_lower in {'các', 'những', 'nào', 'gì', 'bao', 'mấy', 'này', 'đó', 'kia'}:
                category = 'DET'
            elif token_lower in {'không', 'có', 'được', 'gì'}:
                category = 'ADV'
            elif token_lower in {'ai', 'tôi', 'tớ', 'mình', 'nó', 'bạn'}:
                category = 'PRONOUN'
            else:
                category = 'NOUN'
            
            tokens_info.append((token, category))
        
        # Build a parse tree based on the categorized tokens
        children = []
        i = 0
        while i < len(tokens_info):
            token, cat = tokens_info[i]
            
            if cat == 'PUNCT':
                children.append(ParseNode(symbol='PUNCT', word=token))
                i += 1
            elif cat == 'WH_WORD':
                children.append(ParseNode(symbol='WH_WORD', word=token))
                i += 1
            elif cat in ('COURSE_NAME', 'TOPIC', 'ASSIGNMENT', 'LO_ID', 'PRONOUN'):
                children.append(ParseNode(symbol='NP', children=[ParseNode(symbol=cat, word=token)]))
                i += 1
            elif cat == 'NUM':
                # Check if next is "chương" or "tuần"
                np_children = [ParseNode(symbol='NUM', word=token)]
                if i + 1 < len(tokens_info) and tokens_info[i + 1][0] in ('chương', 'tuần'):
                    np_children.append(ParseNode(symbol='NOUN', word=tokens_info[i + 1][0]))
                    i += 2
                else:
                    i += 1
                children.append(ParseNode(symbol='NP', children=np_children))
            elif cat == 'VERB':
                # Collect VP: VERB + everything until next WH_WORD/VERB/PUNCT or end
                vp_children = [ParseNode(symbol='VERB', word=token)]
                i += 1
                # Add the rest of the sentence as flat tokens in VP
                while i < len(tokens_info) and tokens_info[i][1] not in ('PUNCT', 'WH_WORD'):
                    t, c = tokens_info[i]
                    vp_children.append(ParseNode(symbol=c, word=t))
                    i += 1
                children.append(ParseNode(symbol='VP', children=vp_children))
            elif cat == 'DET':
                children.append(ParseNode(symbol='DET', word=token))
                i += 1
            else:  # NOUN or other
                children.append(ParseNode(symbol='NP', children=[ParseNode(symbol='NOUN', word=token)]))
                i += 1
        
        if children:
            # Determine question type
            has_wh = any(c.symbol == 'WH_WORD' for c in children)
            q_type = 'WH_QUESTION' if has_wh else 'YES_NO_QUESTION'
            return ParseNode(symbol=q_type, children=children)
        
        return None
    
    def _parse_question(self) -> Optional[ParseNode]:
        """Parse question structure"""
        # Try WH_QUESTION
        start = self.current_pos
        tree = self._parse_wh_question()
        if tree:
            return tree
        
        # Try YES_NO_QUESTION
        self.current_pos = start
        tree = self._parse_yes_no_question()
        if tree:
            return tree
        
        return None
    
    def _parse_wh_question(self) -> Optional[ParseNode]:
        """Parse WH-question: WH_WORD NP VP ?"""
        children = []
        
        # Parse WH_WORD
        wh_node = self._parse_wh_word()
        if not wh_node:
            return None
        children.append(wh_node)
        
        # Parse NP (may be optional)
        np_node = self._parse_np()
        if np_node:
            children.append(np_node)
        
        # Parse VP
        vp_node = self._parse_vp()
        if vp_node:
            children.append(vp_node)
        
        # Parse question mark
        q_node = self._parse_question_mark()
        if q_node:
            children.append(q_node)
        
        return ParseNode(symbol="WH_QUESTION", children=children) if children else None
    
    def _parse_yes_no_question(self) -> Optional[ParseNode]:
        """Parse yes/no question: NP VP ?"""
        children = []
        
        # Parse NP
        np_node = self._parse_np()
        if not np_node:
            return None
        children.append(np_node)
        
        # Parse VP
        vp_node = self._parse_vp()
        if vp_node:
            children.append(vp_node)
        
        # Parse question mark
        q_node = self._parse_question_mark()
        if q_node:
            children.append(q_node)
        
        return ParseNode(symbol="YES_NO_QUESTION", children=children) if children else None
    
    def _parse_wh_word(self) -> Optional[ParseNode]:
        """Parse WH word"""
        if self.current_pos >= len(self.tokens):
            return None
        
        token, pos = self.tokens[self.current_pos]
        token_lower = token.lower()
        
        # Check if token is a WH word
        wh_indicators = {'môn', 'tuần', 'chương', 'bài', 'tài', 'quy', 'thời', 
                        'deadline', 'ai', 'ở', 'đâu', 'bao', 'có', 'là', 'gì', 'nào',
                        'các', 'những'}
        
        if token_lower in wh_indicators or token_lower in self.wh_words:
            node = ParseNode(symbol="WH_WORD", word=token_lower)
            self.current_pos += 1
            return node
        
        return None
    
    def _parse_np(self) -> Optional[ParseNode]:
        """Parse noun phrase"""
        if self.current_pos >= len(self.tokens):
            return None
        
        token, pos = self.tokens[self.current_pos]
        token_lower = token.lower()
        
        children = []
        
        # Try to parse as various NP types
        # Course name
        if token_lower in self.course_names:
            node = ParseNode(symbol="NP", children=[ParseNode(symbol="COURSE_NAME", word=token_lower)])
            self.current_pos += 1
            return node
        
        # Number (chapter or week)
        if token_lower in self.numbers:
            # Determine if chapter or week based on context
            num_node = ParseNode(symbol="NUM", word=token_lower)
            children.append(num_node)
            self.current_pos += 1
            
            # Check if followed by "chương" or "tuần"
            if self.current_pos < len(self.tokens):
                next_token = self.tokens[self.current_pos][0].lower()
                if next_token == 'chương':
                    children.append(ParseNode(symbol="NOUN", word='chương'))
                    self.current_pos += 1
                    return ParseNode(symbol="NP", children=children)
                elif next_token == 'tuần':
                    children.append(ParseNode(symbol="NOUN", word='tuần'))
                    self.current_pos += 1
                    return ParseNode(symbol="NP", children=children)
            
            return ParseNode(symbol="NP", children=children)
        
        # Noun or pronoun
        if pos in ['NOUN', 'PRONOUN'] or token_lower in {'tôi', 'tớ', 'mình', 'nó', 'bạn'}:
            node = ParseNode(symbol="NP", children=[ParseNode(symbol=pos, word=token_lower)])
            self.current_pos += 1
            return node
        
        # Check for specific patterns
        # Topic (CFG, PCFG, etc.)
        if token_lower in self.topics:
            node = ParseNode(symbol="NP", children=[ParseNode(symbol="TOPIC_NAME", word=token_lower)])
            self.current_pos += 1
            return node
        
        # Assignment (BTL, bài tập lớn)
        if token_lower in self.assignment_names:
            node = ParseNode(symbol="NP", children=[ParseNode(symbol="ASSIGNMENT", word=token_lower)])
            self.current_pos += 1
            return node
        
        # Learning Outcome
        if token_lower.startswith('l.o.') or token_lower.startswith('lo'):
            node = ParseNode(symbol="NP", children=[ParseNode(symbol="LO_ID", word=token_lower)])
            self.current_pos += 1
            return node
        
        return None
    
    def _parse_vp(self) -> Optional[ParseNode]:
        """Parse verb phrase"""
        if self.current_pos >= len(self.tokens):
            return None
        
        children = []
        
        # Parse verb
        token, pos = self.tokens[self.current_pos]
        token_lower = token.lower()
        
        verb_indicators = {'học', 'nói', 'có', 'xuất', 'liên', 'quan', 'cần', 
                          'muốn', 'biết', 'hỏi', 'tra', 'xem', 'tìm', 'yêu', 
                          'cầu', 'sử', 'dụng', 'được', 'nộp', 'kéo', 'dài',
                          'là', 'ở', 'về', 'của', 'với', 'cho'}
        
        if token_lower in verb_indicators or pos == 'VERB':
            verb_node = ParseNode(symbol="VERB", word=token_lower)
            children.append(verb_node)
            self.current_pos += 1
            
            # Try to parse additional elements
            while self.current_pos < len(self.tokens):
                # Check for question mark
                if self.tokens[self.current_pos][0] in ['?', '!']:
                    break
                
                # Try NP
                np_node = self._parse_np()
                if np_node:
                    children.append(np_node)
                    continue
                
                # Try ADJ
                if self.current_pos < len(self.tokens):
                    adj_token = self.tokens[self.current_pos][0].lower()
                    if adj_token in {'gì', 'nào', 'bao', 'nhiêu', 'mấy'}:
                        adj_node = ParseNode(symbol="ADJ", word=adj_token)
                        children.append(adj_node)
                        self.current_pos += 1
                        continue
                
                # Try ADV
                if self.current_pos < len(self.tokens):
                    adv_token = self.tokens[self.current_pos][0].lower()
                    if adv_token in {'không', 'có', 'được', 'gì'}:
                        adv_node = ParseNode(symbol="ADV", word=adv_token)
                        children.append(adv_node)
                        self.current_pos += 1
                        continue
                
                break
            
            return ParseNode(symbol="VP", children=children)
        
        return None
    
    def _parse_question_mark(self) -> Optional[ParseNode]:
        """Parse question mark or exclamation"""
        if self.current_pos >= len(self.tokens):
            return None
        
        token, pos = self.tokens[self.current_pos]
        if token in ['?', '!']:
            self.current_pos += 1
            return ParseNode(symbol="PUNCT", word=token)
        
        return None
    
    def parse_batch(self, sentences: List[str]) -> List[Tuple[Optional[ParseNode], List[str]]]:
        """Parse multiple sentences"""
        results = []
        for sentence in sentences:
            result = self.parse(sentence)
            results.append(result)
        return results
    
    def get_parse_result(self, text: str) -> str:
        """Get parse result as string"""
        tree, errors = self.parse(text)
        
        if tree:
            return str(tree)
        else:
            return "()"


def main():
    """Test parser"""
    parser = Parser()
    
    test_sentences = [
        "Môn NLP có bao nhiêu tín chỉ?",
        "Tuần 3 học gì?",
        "Chương 4 nói về gì?",
        "Deadline BTL là khi nào?",
        "Tài liệu về CFG ở đâu?",
    ]
    
    print("Parser Test Results")
    print("=" * 60)
    
    for sentence in test_sentences:
        print(f"\nInput: {sentence}")
        result = parser.get_parse_result(sentence)
        print(f"Output: {result}")
        print("-" * 60)


if __name__ == "__main__":
    main()
