"""
Preprocessing module for Vietnamese text
Handles tokenization, normalization, and basic NLP tasks
"""

import re
from typing import List, Dict, Tuple
import unicodedata


class Preprocessor:
    """Vietnamese text preprocessor for Course Assistant"""
    
    def __init__(self):
        # Vietnamese stopwords
        self.stopwords = {
            'có', 'và', 'của', 'là', 'được', 'trong', 'với', 
            'cho', 'hay', 'không', 'các', 'những', 'nào', 'gì',
            'ở', 'đâu', 'bao', 'nhiêu', 'mấy', 'này', 'kia', 
            'đó', 'về', 'ra', 'vào', 'từ', 'lên', 'xuống',
            'theo', 'tại', 'trên', 'dưới', 'bên', 'ngoài', 'trong'
        }
        
        # Normalization mappings
        self.vietnamese_mappings = {
            'òa': 'oà', 'óa': 'oá', 'ỏa': 'oả', 'õa': 'oã',
            'ọa': 'oạ', 'èè': 'è', 'éè': 'é', 'ẻè': 'ẻ', 'ẽè': 'ẽ', 'ẹè': 'ẹ',
            # Add more mappings as needed
        }
    
    def normalize(self, text: str) -> str:
        """
        Normalize Vietnamese text:
        - Lowercase
        - Remove extra spaces
        - Handle unicode normalization
        """
        # Unicode NFC normalization
        text = unicodedata.normalize('NFC', text)
        
        # Lowercase
        text = text.lower()
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        return text
    
    def tokenize(self, text: str) -> List[str]:
        """
        Simple tokenization for Vietnamese text
        Preserves special patterns like L.O.X.Y
        """
        import re
        # Normalize first
        text = self.normalize(text)
        
        # Protect L.O. patterns before tokenization
        text = re.sub(r'l\.o\.(\d+)\.(\d+)', r'lo_\1_\2', text)
        text = re.sub(r'l\.o\.(\d+)', r'lo_\1', text)
        
        # Split by whitespace and punctuation
        tokens = re.findall(r'\b\w+\b', text)
        
        return tokens
    
    def remove_stopwords(self, tokens: List[str]) -> List[str]:
        """Remove Vietnamese stopwords"""
        return [t for t in tokens if t.lower() not in self.stopwords]
    
    def extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from text (remove stopwords)"""
        tokens = self.tokenize(text)
        return self.remove_stopwords(tokens)
    
    def get_token_pos(self, token: str) -> str:
        """Get POS tag for a single token"""
        return VIETNAMESE_POS_TAGS.get(token.lower(), 'X')
    
    def preprocess(self, text: str) -> Dict[str, any]:
        """
        Full preprocessing pipeline
        Returns dict with tokens, normalized text, and keywords
        """
        normalized = self.normalize(text)
        tokens = self.tokenize(text)
        keywords = self.remove_stopwords(tokens)
        
        return {
            'original': text,
            'normalized': normalized,
            'tokens': tokens,
            'keywords': keywords
        }


# Rule-based POS tagger for Vietnamese (simplified)
VIETNAMESE_POS_TAGS = {
    # Common words
    'môn': 'NOUN', 'nlp': 'NOUN', 'co3085': 'NOUN',
    'tín': 'NOUN', 'chỉ': 'NOUN', 'học': 'VERB',
    'chương': 'NOUN', 'tuần': 'NOUN', 'bài': 'NOUN',
    'tập': 'NOUN', 'lớn': 'ADJ', 'btl': 'NOUN',
    'tài': 'NOUN', 'liệu': 'NOUN', 'quy': 'NOUN',
    'định': 'NOUN', 'deadline': 'NOUN', 'hạn': 'NOUN',
    'nộp': 'VERB', 'có': 'VERB', 'không': 'ADV',
    'bao': 'ADV', 'nhiêu': 'DET', 'gì': 'PRON',
    'nào': 'DET', 'ở': 'PREP', 'đâu': 'ADV',
    'về': 'PREP', 'là': 'VERB', 'được': 'AUX',
    'thông': 'NOUN', 'tin': 'NOUN', 'nói': 'VERB',
    'về': 'PREP', 'hỏi': 'VERB', 'hỏi': 'VERB',
    'yêu': 'VERB', 'cầu': 'NOUN', 'cần': 'VERB',
    'muốn': 'VERB', 'biết': 'VERB', 'tra': 'VERB',
    'cứu': 'VERB', 'xem': 'VERB', 'kiểm': 'VERB',
    'tra': 'VERB', 'liên': 'ADJ', 'quan': 'ADJ',
    'tôi': 'PRON', 'tôi': 'PRON', 'mình': 'PRON',
    'anh': 'PRON', 'chị': 'PRON', 'em': 'PRON',
    'ai': 'PRON', 'đó': 'DET', 'này': 'DET',
    'kia': 'DET', 'nọ': 'DET',
    
    # Numbers
    '1': 'NUM', '2': 'NUM', '3': 'NUM', '4': 'NUM',
    '5': 'NUM', '6': 'NUM', '7': 'NUM', '8': 'NUM',
    '9': 'NUM', '10': 'NUM', '11': 'NUM', '12': 'NUM',
    '15': 'NUM', '60': 'NUM', '90': 'NUM',
    
    # CFG, PCFG, etc.
    'cfg': 'NOUN', 'pcfg': 'NOUN', 'pos': 'NOUN',
    'parsing': 'NOUN', 'semantic': 'NOUN', 'syntax': 'NOUN',
    
    # Parts
    'part': 'NOUN', 'i': 'NUM', 'ii': 'NUM', 'iii': 'NUM',
}


def pos_tag(tokens: List[str]) -> List[Tuple[str, str]]:
    """
    Simple rule-based POS tagging for Course Assistant domain
    Returns list of (token, pos_tag) tuples
    """
    tagged = []
    for token in tokens:
        token_lower = token.lower()
        pos = VIETNAMESE_POS_TAGS.get(token_lower, 'X')  # X = unknown
        tagged.append((token, pos))
    return tagged


def get_token_pos(token: str) -> str:
    """Get POS tag for a single token"""
    return VIETNAMESE_POS_TAGS.get(token.lower(), 'X')
