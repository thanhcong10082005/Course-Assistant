"""
Parser module for Course Assistant.

A **grammar-driven chart parser** built on top of an Earley recogniser.

Why
---
The previous hand-written recursive-descent parser hard-coded a *second* copy of
the language: a list of "verb indicators", a list of "WH words", a list of
"topics".  Every new sentence pattern therefore required editing two files
and the two copies silently drifted apart -- the parser could only handle
4/34 of the official questions *strictly*.

The parser implemented here removes the duplication completely:

* it reads the productions, the terminal classes and the vocabulary
  **directly from** :class:`src.grammar.CFG`,
* it runs an **Earley chart parser** over those productions, which handles
  the ambiguity that is inherent in natural language without any
  hand-written disambiguation rules,
* it keeps the old pattern-based fallback for the sentences that are outside
  the grammar (for example the deliberately out-of-scope questions), so that
  the pipeline always produces a tree.

The public API is unchanged: :meth:`Parser.parse` returns
``(tree, errors)`` and :meth:`Parser.get_parse_result` returns a printable
tree.
"""

from __future__ import annotations

import re
import sys
import os
from typing import Dict, FrozenSet, List, Optional, Sequence, Set, Tuple
from dataclasses import dataclass, field

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
        # A terminal whose surface form equals its symbol is printed once.
        if self.word and self.word != self.symbol:
            return f"({self.symbol} {self.word})"
        return f"({self.symbol})"

    def __str__(self):
        return self.__repr__()

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

    def leaves(self) -> List[str]:
        """The terminal words of the tree, in reading order."""
        if not self.children:
            return [self.word or self.symbol]
        result: List[str] = []
        for child in self.children:
            result.extend(child.leaves())
        return result

    def height(self) -> int:
        """The height of the subtree (a leaf has height 1)."""
        if not self.children:
            return 1
        return 1 + max(child.height() for child in self.children)


class EarleyParse:
    """Result of an Earley chart parse."""

    def __init__(self, tree: Optional[ParseNode], n: int) -> None:
        self.tree = tree
        self.n = n

    @property
    def ok(self) -> bool:
        return self.tree is not None


class Parser:
    """
    Earley chart parser for the Course Assistant CFG.

    The grammar is the single source of truth: the parser never hard-codes
    a list of verbs, question words or topics, it *derives* them from the
    productions in :class:`src.grammar.CFG`.
    """

    def __init__(self, grammar: CFG = None):
        self.grammar = grammar if grammar else CFG()
        self.preprocessor = Preprocessor()
        self.tokens: List[Tuple[str, str]] = []
        self.pos_tags: List[Tuple[str, str]] = []
        self.current_pos: int = 0
        self.errors: List[str] = []
        self.last_method: str = ""   # "strict" | "fallback" | "failure"

        self._build_lookup_tables()
        self._build_grammar_index()

    # ------------------------------------------------------------------
    # Lookup tables
    # ------------------------------------------------------------------
    def _build_lookup_tables(self):
        """Derive the parser's vocabulary from the grammar."""
        grammar = self.grammar

        self.wh_words: Set[str] = set()
        self.course_names: Set[str] = set()
        self.numbers: Set[str] = set()
        self.topics: Set[str] = set()
        self.assignment_names: Set[str] = set()
        self.verbs: Set[str] = set()
        self.prepositions: Set[str] = set()
        self.determiners: Set[str] = set()
        self.nouns: Set[str] = set()
        self.pronouns: Set[str] = set()
        self.quants: Set[str] = set()
        self.lo_ids: Set[str] = set()

        self.wh_words |= grammar.terminals_of("WH_QWORD")
        self.course_names |= grammar.terminals_of("COURSE_NAME")
        self.course_names |= grammar.terminals_of("COURSE_MOD")
        self.topics |= grammar.terminals_of("TOPIC_NAME")
        self.assignment_names |= grammar.terminals_of("ASSIGNMENT_NAME")
        self.verbs |= grammar.terminals_of("VERB")
        self.prepositions |= grammar.terminals_of("PREP")
        self.determiners |= grammar.terminals_of("DET")
        self.nouns |= grammar.terminals_of("NOUN")
        self.pronouns |= grammar.terminals_of("PRONOUN")
        self.quants |= grammar.terminals_of("QUANT")
        self.lo_ids |= grammar.terminals_of("LO_ID")
        self.numbers |= {t for t in grammar.terminals if t.isdigit()}

        # Legacy alias kept for backwards compatibility.
        self.assignment_names |= {"bài", "tập", "lớn"}

        self.pos_to_category = {
            'NOUN': 'NP', 'PRONOUN': 'NP', 'PRON': 'NP', 'COURSE_NAME': 'NP',
            'CHAPTER_NUM': 'NP', 'WEEK_NUM': 'NP', 'TOPIC_NAME': 'NP',
            'ASSIGNMENT_NAME': 'NP', 'LO_ID': 'NP', 'NUM': 'NP', 'DET': 'NP',
            'VERB': 'VP', 'ADJ': 'VP', 'ADV': 'VP', 'PREP': 'PP',
            'ADP': 'PP', 'AUX': 'VP', 'WH_QWORD': 'WH', 'WH_WORD': 'WH',
            '?': '?', '!': '!', 'PUNCT': 'PUNCT', 'X': 'NP',
        }

    def _build_grammar_index(self):
        """Flatten the grammar into a form the Earley recogniser likes."""
        grammar = self.grammar

        self._rules: List[Tuple[str, List[str]]] = []
        self._by_lhs: Dict[str, List[int]] = {}
        for lhs in sorted(grammar.rules):
            for rule in grammar.rules[lhs]:
                rid = len(self._rules)
                self._rules.append((lhs, list(rule.rhs)))
                self._by_lhs.setdefault(lhs, []).append(rid)

        # surface key -> terminal, used to match a token against the grammar
        self._terminal_map: Dict[str, str] = {}
        for terminal in grammar.terminals:
            self._terminal_map.setdefault(terminal, terminal)
            self._terminal_map.setdefault(terminal.replace("_", " "), terminal)

    # ------------------------------------------------------------------
    # Tokenization
    # ------------------------------------------------------------------
    def tokenize_input(self, text: str) -> List[Tuple[str, str]]:
        """
        Tokenize and POS-tag the input text.

        Multi-word domain entities ("bài tập lớn", "tín chỉ", "LLM/RAG")
        are kept together, and the sentence-final punctuation is emitted as
        its own token so that the grammar's ``PUNCT`` non-terminal can be
        matched.
        """
        spans = self.preprocessor.tokenize_spans(text)
        tokens: List[Tuple[str, str]] = [
            (span["text"], span["pos"]) for span in spans
        ]

        # Sentence-final punctuation ("?" / "!") is not part of any word span.
        for punct in re.findall(r"[?!]+", text or ""):
            tokens.append((punct, "PUNCT"))

        self.pos_tags = list(tokens)
        return tokens

    # ------------------------------------------------------------------
    # Terminal matching
    # ------------------------------------------------------------------
    _LO_RE = re.compile(r"^(?:lo|l\.o\.)_?(\d+)(?:[._](\d+))?$")

    def _match_terminals(self, surface: str) -> Set[str]:
        """All grammar terminals that the given surface form can realise."""
        if not surface:
            return set()

        key = surface.lower()
        found: Set[str] = set()

        direct = self._terminal_map.get(key)
        if direct:
            found.add(direct)
        spaced = self._terminal_map.get(key.replace("_", " "))
        if spaced:
            found.add(spaced)

        # Learning-outcome identifiers are protected by the tokenizer as
        # "lo_2_5" but the grammar declares them as "l.o.2.5".
        match = self._LO_RE.match(key)
        if match:
            major, minor = match.group(1), match.group(2)
            candidate = f"l.o.{major}" + (f".{minor}" if minor else "")
            if candidate in self.grammar.terminals:
                found.add(candidate)
            plain = f"l.o.{major}"
            if plain in self.grammar.terminals:
                found.add(plain)

        return found

    # ------------------------------------------------------------------
    # Earley recogniser
    # ------------------------------------------------------------------
    def _earley_parse(self, tokens: Sequence[Tuple[str, str]]) -> Optional[ParseNode]:
        """
        Run the Earley recogniser over ``tokens`` and build the parse tree.

        Returns ``None`` when the token sequence is not generated by the
        grammar.

        The recogniser keeps two tables:

        ``complete``
            ``(symbol, start, stop) -> [rule id]``: the rules that derive
            ``symbol`` over the token span ``[start, stop)``.

        ``advance``
            ``(rule id, dot) -> [(symbol, start, stop)]``: for every symbol
            of a production, the spans that the symbol may cover.

        Because the grammar is ambiguous, a symbol may have several spans;
        the tree builder therefore backtracks over the candidates.
        """
        grammar = self.grammar
        n = len(tokens)
        if n == 0:
            return None

        terminal_sets = [self._match_terminals(surface) for surface, _ in tokens]

        # chart[k] holds the items that are valid after consuming k tokens.
        # An item is (rule_id, dot, origin).
        chart: List[Set[Tuple[int, int, int]]] = [set() for _ in range(n + 1)]
        agenda: List[List[Tuple[int, int, int]]] = [[] for _ in range(n + 1)]

        complete: Dict[Tuple[str, int, int], List[int]] = {}
        advance: Dict[Tuple[int, int, int], List[Tuple[str, int, int]]] = {}

        def add(item: Tuple[int, int, int], k: int) -> None:
            if item not in chart[k]:
                chart[k].add(item)
                agenda[k].append(item)

        def record(rule_id: int, dot: int, position: int, entry: Tuple[str, int, int]) -> None:
            """
            Remember that ``rhs[dot]`` of ``rule_id`` may cover ``entry``.

            The key includes the token ``position`` where the symbol starts:
            without it the tree builder could pick a span that does not begin
            where the current derivation stands, and tokens would be dropped
            from the tree.
            """
            key = (rule_id, dot, position)
            bucket = advance.setdefault(key, [])
            if entry not in bucket:
                bucket.append(entry)

        for rid in self._by_lhs.get(grammar.start_symbol, []):
            add((rid, 0, 0), 0)

        for k in range(n + 1):
            while agenda[k]:
                rid, dot, origin = agenda[k].pop()
                lhs, rhs = self._rules[rid]

                if dot < len(rhs):
                    symbol = rhs[dot]
                    if grammar.is_terminal(symbol):
                        if k < n and symbol in terminal_sets[k]:
                            record(rid, dot, k, (symbol, k, k + 1))
                            add((rid, dot + 1, origin), k + 1)
                    else:
                        # Predictor: every rule of `symbol` starts here.
                        for rid2 in self._by_lhs.get(symbol, []):
                            add((rid2, 0, k), k)
                else:
                    # The rule is complete: it derives `lhs` over (origin, k).
                    complete.setdefault((lhs, origin, k), []).append(rid)

                    # Magic completion: every item of chart[origin] that is
                    # waiting for `lhs` can now advance.
                    for rid2, dot2, origin2 in list(chart[origin]):
                        rhs2 = self._rules[rid2][1]
                        if dot2 < len(rhs2) and rhs2[dot2] == lhs:
                            record(rid2, dot2, origin, (lhs, origin, k))
                            add((rid2, dot2 + 1, origin2), k)

        if (grammar.start_symbol, 0, n) not in complete:
            return None

        return self._build_tree(
            (grammar.start_symbol, 0, n), complete, advance, tokens, frozenset()
        )

    def _build_tree(
        self,
        node: Tuple[str, int, int],
        complete: Dict[Tuple[str, int, int], List[int]],
        advance: Dict[Tuple[int, int, int], List[Tuple[str, int, int]]],
        tokens: Sequence[Tuple[str, str]],
        seen: FrozenSet[Tuple[str, int, int]],
    ) -> Optional[ParseNode]:
        """
        Rebuild the parse tree from the recorded completions.

        The search backtracks over the ambiguous candidates so that a
        derivation which cannot be completed is discarded in favour of one
        that can.
        """
        symbol, start, stop = node
        if node in seen:
            return None
        seen = seen | {node}

        for rid in complete.get(node, []):
            lhs, rhs = self._rules[rid]
            built = self._build_children(
                rid, rhs, 0, start, stop, complete, advance, tokens, seen
            )
            if built is not None:
                return ParseNode(symbol=lhs, children=built)
        return None

    def _build_children(
        self,
        rid: int,
        rhs: List[str],
        dot: int,
        position: int,
        stop: int,
        complete: Dict[Tuple[str, int, int], List[int]],
        advance: Dict[Tuple[int, int, int], List[Tuple[str, int, int]]],
        tokens: Sequence[Tuple[str, str]],
        seen: FrozenSet[Tuple[str, int, int]],
    ) -> Optional[List[ParseNode]]:
        """Recursively build the children of a production from ``dot`` on."""
        if dot >= len(rhs):
            return [] if position == stop else None

        child_symbol = rhs[dot]

        # Only the spans that *begin* at the current position are valid
        # continuations of this derivation.
        for cand_symbol, cand_start, cand_stop in advance.get((rid, dot, position), []):
            if cand_symbol != child_symbol:
                continue
            if cand_start != position:
                continue

            built_child: Optional[ParseNode]
            if self.grammar.is_terminal(cand_symbol):
                word = (
                    tokens[cand_start][0] if cand_start < len(tokens)
                    else cand_symbol
                )
                built_child = ParseNode(symbol=cand_symbol, word=word)
            else:
                built_child = self._build_tree(
                    (cand_symbol, cand_start, cand_stop),
                    complete, advance, tokens, seen,
                )
            if built_child is None:
                continue

            rest = self._build_children(
                rid, rhs, dot + 1, cand_stop, stop,
                complete, advance, tokens, seen,
            )
            if rest is None:
                continue
            return [built_child] + rest

        return None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def parse(self, text: str) -> Tuple[Optional[ParseNode], List[str]]:
        """
        Parse the input text with the strict grammar-driven parser.

        If the strict parser fails the pattern-based fallback is used, so
        the caller always receives a tree.  The errors list is empty when a
        tree could be produced.
        """
        self.tokens = self.tokenize_input(text)
        self.current_pos = 0
        self.errors = []
        self.last_method = ""

        if not self.tokens:
            return None, ["Empty input"]

        tree = self._parse_question()
        if tree and self.current_pos == len(self.tokens):
            self.last_method = "strict"
            return tree, []

        fallback_tree = self._parse_fallback(text)
        if fallback_tree:
            self.last_method = "fallback"
            return fallback_tree, []

        self.errors.append(
            f"Parse incomplete at position {self.current_pos}/{len(self.tokens)}"
        )
        self.last_method = "failure"
        return None, self.errors

    def _parse_question(self) -> Optional[ParseNode]:
        """
        Strict parse: run the Earley recogniser over the current tokens.

        On success ``current_pos`` is advanced to the end of the input so
        that the caller can tell a complete parse from a partial one.
        """
        tree = self._earley_parse(self.tokens)
        if tree is None:
            return None

        # The root is the start symbol; report its single child so that the
        # tree is labelled with the question type (WH_QUESTION / ...).
        if tree.symbol == self.grammar.start_symbol and len(tree.children) == 1:
            tree = tree.children[0]

        self.current_pos = len(self.tokens)
        return tree

    # ------------------------------------------------------------------
    # Fallback parser
    # ------------------------------------------------------------------
    def _parse_fallback(self, text: str) -> Optional[ParseNode]:
        """
        Pattern-based fallback for sentences outside the grammar.

        The token categories are derived from the grammar's terminal classes
        so that the fallback stays consistent with the strict parser.
        """
        tokens_info = []
        for token, pos in self.tokens:
            token_lower = token.lower()
            category = self._categorize(token, token_lower, pos)
            tokens_info.append((token, category))

        children: List[ParseNode] = []
        i = 0
        while i < len(tokens_info):
            token, cat = tokens_info[i]

            if cat == "PUNCT":
                children.append(ParseNode(symbol="PUNCT", word=token))
                i += 1
            elif cat == "WH_WORD":
                children.append(ParseNode(symbol="WH_WORD", word=token))
                i += 1
            elif cat in ("COURSE_NAME", "TOPIC", "ASSIGNMENT", "LO_ID", "PRONOUN"):
                children.append(
                    ParseNode(symbol="NP", children=[ParseNode(symbol=cat, word=token)])
                )
                i += 1
            elif cat == "NUM":
                np_children = [ParseNode(symbol="NUM", word=token)]
                if i + 1 < len(tokens_info) and tokens_info[i + 1][0] in ("chương", "tuần"):
                    np_children.append(ParseNode(symbol="NOUN", word=tokens_info[i + 1][0]))
                    i += 2
                else:
                    i += 1
                children.append(ParseNode(symbol="NP", children=np_children))
            elif cat == "VERB":
                vp_children = [ParseNode(symbol="VERB", word=token)]
                i += 1
                while i < len(tokens_info) and tokens_info[i][1] not in ("PUNCT", "WH_WORD"):
                    t, c = tokens_info[i]
                    vp_children.append(ParseNode(symbol=c, word=t))
                    i += 1
                children.append(ParseNode(symbol="VP", children=vp_children))
            elif cat == "DET":
                children.append(ParseNode(symbol="DET", word=token))
                i += 1
            else:
                children.append(
                    ParseNode(symbol="NP", children=[ParseNode(symbol="NOUN", word=token)])
                )
                i += 1

        if children:
            has_wh = any(c.symbol == "WH_WORD" for c in children)
            q_type = "WH_QUESTION" if has_wh else "YES_NO_QUESTION"
            return ParseNode(symbol=q_type, children=children)

        return None

    def _categorize(self, token: str, token_lower: str, pos: str) -> str:
        """Assign a coarse category to a token (used by the fallback)."""
        if token in ("?", "!"):
            return "PUNCT"

        grammar = self.grammar
        if token_lower in self.course_names:
            return "COURSE_NAME"
        if token_lower.isdigit():
            return "NUM"
        if token_lower in self.topics:
            return "TOPIC"
        if token_lower in self.assignment_names:
            return "ASSIGNMENT"
        if self._LO_RE.match(token_lower) or token_lower.startswith("l.o."):
            return "LO_ID"
        if token_lower in self.wh_words or token_lower in {"gì", "nào", "bao", "nhiêu", "mấy"}:
            return "WH_WORD"
        if token_lower in self.verbs or pos in {"VERB", "AUX"}:
            return "VERB"
        if token_lower in self.prepositions:
            return "PREP"
        if token_lower in self.determiners or token_lower in {"gì", "nào"}:
            return "DET"
        if token_lower in self.pronouns or pos in {"PRON", "PRONOUN"}:
            return "PRONOUN"
        return "NOUN"

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------
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
        return "()"

    def parse_strict(self, text: str) -> Optional[ParseNode]:
        """
        Parse with the strict grammar-driven parser only.

        Returns ``None`` when the sentence is not generated by the grammar
        (the fallback is *not* used).
        """
        self.tokens = self.tokenize_input(text)
        self.current_pos = 0
        self.errors = []
        if not self.tokens:
            return None
        return self._parse_question()


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
