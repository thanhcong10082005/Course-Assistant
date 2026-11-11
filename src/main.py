"""
Course Assistant - Main Application
Integrates all NLP components for the Course Assistant system.

Pipeline
--------
::

    Preprocessing  ->  Parsing  ->  Dialogue Context  ->  Semantic Analysis
                     ->  Knowledge Base  ->  Answer

:class:`CourseAssistant` owns a real :class:`~src.dialogue.DialogueManager`
instead of a plain dictionary of strings, so that

* the discourse state survives across the turns of a conversation,
* the contextual references ("nó", "phần này", "chương sau") are resolved by
  the dialogue manager *before* the semantic analyzer runs,
* a query whose reference cannot be resolved is answered with a request for
  clarification (``CONTEXT_DEPENDENT``) instead of a confident guess.

Entry points
------------
``python -m src.main --mode demo``
    A narrated walk-through of the whole pipeline.
``python -m src.main --mode interactive``
    A conversational session with ``/context`` and ``/reset``.
``python -m src.main --mode generate``
    Writes the nine artefacts of ``output/`` in one go.
"""

import os
import sys
from typing import List, Tuple, Dict, Optional

from .preprocessing import Preprocessor
from .grammar import CFG, generate_template_sentences
from .parser import Parser
from .semantic import SemanticAnalyzer, SemanticRepresentation, IntentType
from .knowledge_base import KnowledgeBase
from .dialogue import DialogueManager

# The nine artefacts required by the assignment.
OUTPUT_FILES = (
    "grammar.txt",
    "samples.txt",
    "parse-results.txt",
    "semantic.txt",
    "intent-entity.txt",
    "query.txt",
    "answer.txt",
    "dialogue.txt",
    "evaluation.txt",
)

# The official demonstration dialogues: (turn 1, turn 2).  The second turn
# of each dialogue contains a contextual reference that can only be resolved
# against the state built by the first turn.
DEMO_DIALOGUES = (
    ("Tuần 3 học gì?", "Tài liệu của chương này là gì?"),
    ("Chương 4 nói về gì?", "Nó có liên quan đến parsing không?"),
    ("Chương 11 có hỏi đáp không?", "Còn chương sau?"),
    ("Bài tập lớn có phần parser không?", "Phần này cần xuất file gì?"),
    ("L.O.2.5 học về gì?", "Nội dung này nằm ở chương nào?"),
)

# The sentences parsed and analysed in the output artefacts.
ANALYSIS_SENTENCES = (
    "Môn NLP có bao nhiêu tín chỉ?",
    "CO3085 có mấy tín chỉ?",
    "Môn học gồm những phần nào?",
    "Tuần 3 học gì?",
    "Chương 4 học vào tuần nào?",
    "Chương nào nói về CFG?",
    "PCFG được học ở đâu?",
    "Chương nào nói về semantic grammar?",
    "L.O.2.5 là gì?",
    "L.O.4.2 liên quan đến nội dung nào?",
    "Bài tập lớn yêu cầu xây dựng những gì?",
    "Phần I của bài tập lớn là gì?",
    "Bài tập lớn có phần hỏi đáp không?",
    "Có được dùng LLM/RAG không?",
    "Quy định về sử dụng AI là gì?",
    "Midterm bao lâu?",
    "Final kéo dài bao lâu?",
    "Tài liệu tham khảo về statistical NLP là gì?",
    "Tài liệu nào liên quan đến Python NLP?",
    "Chương 12 nói về gì?",
    "Chương nào học về reference?",
    "Chương nào học về question answering?",
    "Chương nào học về selectional restriction?",
    "Chương 10 có những phương pháp gì?",
    "Chương 11 có liên quan đến hỏi đáp không?",
    "Ai là giảng viên môn này?",
    "Hạn nộp bài tập lớn là khi nào?",
    "Chương 4 nói về gì?",
    "Nó có liên quan đến parsing không?",
    "Còn chương sau?",
    "Bài tập lớn có phần parser không?",
    "Phần này cần xuất file gì?",
    "Hôm nay ở TP.HCM có mưa không?",
    "Ai là tổng thống của Pháp?",
    "Hãy giải bài tập xác suất này giúp tôi.",
)


def project_root() -> str:
    """The absolute path of the repository root."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class CourseAssistant:
    """
    Main Course Assistant System
    Integrates: Preprocessing -> Parsing -> Semantic Analysis -> Knowledge Base -> Answer
    """

    def __init__(self, data_dir: str = None):
        """
        Initialize Course Assistant

        Args:
            data_dir: Directory containing course data files
        """
        self.preprocessor = Preprocessor()
        self.grammar = CFG()
        self.parser = Parser(self.grammar)
        self.semantic_analyzer = SemanticAnalyzer()
        self.knowledge_base = KnowledgeBase()

        # Dialogue context storage: a real dialogue manager, not a
        # dictionary of strings.  The manager needs the weekly schedule so
        # that "chương này" can be resolved to the chapter of the current
        # week ("Tuần 3 học gì?" -> "chương 3").
        self.dialogue_manager = DialogueManager(schedule=self.knowledge_base.schedule)
        self.dialogue_context: Dict[str, any] = {}

        # Set data directory
        if data_dir:
            self.data_dir = data_dir
        else:
            # Default to parent directory's data folder
            self.data_dir = os.path.join(project_root(), 'data')

    # ------------------------------------------------------------------
    # Core pipeline
    # ------------------------------------------------------------------
    def process_query(self, query: str) -> Dict[str, any]:
        """
        Process a user query through the full NLP pipeline

        The query is analysed **without** the dialogue context.  A query
        whose meaning depends on the previous turn therefore cannot be
        answered here: its intent is reported as ``CONTEXT_DEPENDENT`` and
        the answer asks the user for the missing context.

        Args:
            query: User query in Vietnamese

        Returns:
            Dictionary containing:
            - original_query: Original query
            - normalized_query: Normalized query
            - parse_result: Parse tree result
            - semantic_rep: Semantic representation
            - answer: Generated answer
        """
        result = {
            'original_query': query,
            'normalized_query': '',
            'parse_result': None,
            'semantic_rep': None,
            'intent': None,
            'entities': {},
            'answer': ''
        }

        # Step 1: Preprocessing
        preprocessed = self.preprocessor.preprocess(query)
        result['normalized_query'] = preprocessed['normalized']
        result['tokens'] = preprocessed['tokens']

        # Step 2: Parsing (optional - for grammar demonstration)
        parse_result = self.parser.get_parse_result(query)
        result['parse_result'] = parse_result

        # Step 3: Semantic Analysis
        #
        # A query that contains a contextual reference but is asked on its
        # own cannot be interpreted: it needs the discourse state.  The
        # dialogue manager tells us whether such a reference is present.
        #
        # Two situations are distinguished:
        #
        # * a **live dialogue session** -- the reference can be resolved
        #   against the state of the previous turns, so the question is
        #   answered normally (this is what
        #   :meth:`process_dialogue` does);
        # * a **standalone query** -- the reference cannot be resolved.  The
        #   intent is reported as ``CONTEXT_DEPENDENT`` so that the caller
        #   asks for clarification, but the most likely referent is still
        #   reported in the entities (the official test set expects this:
        #   "Nó có liên quan đến parsing không?" -> ``CH04``).
        context: Dict[str, any] = {}
        if self.dialogue_manager.has_reference(query):
            # The reference is resolved against the discourse state.  The
            # resolution yields the most likely referent of the question
            # ("nó" -> CH04, "chương sau" -> CH12, "phần này" -> PART_I).
            _, resolved = self.dialogue_manager.resolve_reference(query)
            context.update({
                key: value
                for key, value in resolved.items()
                if key not in {"inferred_entities", "unresolved_reference"}
            })

            if not self.dialogue_manager.has_active_session:
                # The question was asked on its own: the referent can only be
                # *assumed*.  The intent therefore stays CONTEXT_DEPENDENT so
                # that the caller asks for clarification, but the presumed
                # referent is still reported in the entities.
                context['context_dependent'] = True

        sem_rep = self.semantic_analyzer.analyze(query, preprocessed['tokens'],
                                                  context=context)
        result['semantic_rep'] = str(sem_rep)
        result['intent'] = sem_rep.intent.value
        result['entities'] = sem_rep.entities

        # Step 4: Query Knowledge Base
        result['answer'] = self._answer_for(sem_rep.intent, sem_rep.entities)

        # Step 5: Remember the entities of this turn so that a later
        # question can refer to them ("Nó ...", "Phần này ...").
        self.dialogue_manager.note_context(sem_rep.entities, query)

        return result

    # ------------------------------------------------------------------
    # Dialogue pipeline
    # ------------------------------------------------------------------
    def process_dialogue(self, user_input: str, context: Dict = None) -> Tuple[str, Dict]:
        """
        Process a dialogue turn with the discourse context.

        The reference resolution happens *before* the semantic analysis so
        that the analyzer sees a self-contained question.

        Args:
            user_input: User message
            context: Previous dialogue context (optional).  When omitted the
                assistant uses its own :class:`DialogueManager`.

        Returns:
            Tuple of (answer, new_context)
        """
        current_context = context if context is not None else self.dialogue_context

        # Step 1: Resolve the contextual references against the discourse
        # state that was built by the previous turns.
        resolved_input, resolved_entities = self.dialogue_manager.resolve_reference(
            user_input
        )

        # Step 2: Preprocessing + semantic analysis on the resolved query.
        preprocessed = self.preprocessor.preprocess(resolved_input)
        sem_rep = self.semantic_analyzer.analyze(
            resolved_input,
            preprocessed['tokens'],
            context=resolved_entities,
        )

        # Step 3: Answer.
        answer = self._answer_for(sem_rep.intent, sem_rep.entities)

        # Step 4: Update the discourse state.
        self.dialogue_manager.update_context(
            sem_rep.intent.value,
            sem_rep.entities,
            user_input,
        )

        # Remember the interpretation of this turn: a later turn that
        # refers back to it ("nó") can then be answered consistently.
        self.dialogue_manager.remember_turn(
            user_input, sem_rep.intent.value, sem_rep.entities
        )

        # Keep the legacy dictionary in sync so that the old API keeps
        # working for the callers that use it.
        if sem_rep.entities.get('chapter'):
            current_context['last_chapter'] = sem_rep.entities['chapter']
        if sem_rep.entities.get('topic'):
            current_context['last_topic'] = sem_rep.entities['topic']
        if sem_rep.entities.get('week'):
            current_context['last_week'] = sem_rep.entities['week']
        if sem_rep.entities.get('part'):
            current_context['last_part'] = sem_rep.entities['part']
        current_context['turn'] = self.dialogue_manager.state.turn
        current_context['last_intent'] = sem_rep.intent.value
        # The entities of the turn are exposed as well so that a caller can
        # check what the turn was understood as.
        current_context['entities'] = dict(sem_rep.entities)

        return answer, current_context

    def reset_dialogue(self) -> None:
        """Clear the discourse context."""
        self.dialogue_manager.reset()
        self.dialogue_context = {}

    def get_dialogue_state(self) -> Dict:
        """The summary of the current discourse state."""
        return self.dialogue_manager.get_state_summary()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _answer_for(self, intent: IntentType, entities: Dict) -> str:
        """The answer text for a resolved intent."""
        if intent == IntentType.CONTEXT_DEPENDENT:
            return self.knowledge_base.ask_for_clarification()
        if intent == IntentType.UNKNOWN:
            return self.knowledge_base.unknown_answer()
        return self.knowledge_base.query(intent.value, entities)

    # ------------------------------------------------------------------
    # Batch helpers
    # ------------------------------------------------------------------
    def generate_grammar_sentences(self, max_count: int = 10000) -> List[str]:
        """
        Generate sentences from grammar

        Args:
            max_count: Maximum number of sentences to generate

        Returns:
            List of generated sentences
        """
        return self.grammar.generate_all_sentences(max_sentences=max_count)

    def parse_sentences(self, sentences: List[str]) -> List[str]:
        """
        Parse multiple sentences

        Args:
            sentences: List of sentences to parse

        Returns:
            List of parse results
        """
        results = []
        for sentence in sentences:
            result = self.parser.get_parse_result(sentence)
            results.append(result)
        return results

    def run_interactive(self):
        """Run Course Assistant in interactive mode"""
        print("=" * 70)
        print("Course Assistant - Hệ thống hỗ trợ học tập môn NLP")
        print("=" * 70)
        print("Lệnh: /context (xem ngữ cảnh) · /reset (xoá ngữ cảnh) · exit|quit (thoát)")
        print("-" * 70)

        context = {}

        while True:
            try:
                user_input = input("\nBạn: ").strip()

                if not user_input:
                    continue

                command = user_input.lower()
                if command in ('exit', 'quit', 'thoát'):
                    print("\nCảm ơn bạn đã sử dụng Course Assistant!")
                    break

                if command == '/context':
                    print("\n[NGỮ CẢNH HIỆN TẠI]")
                    print(self._format_state(self.get_dialogue_state()))
                    continue

                if command == '/reset':
                    self.reset_dialogue()
                    context = {}
                    print("Đã xoá ngữ cảnh.")
                    continue

                # The reference has to be resolved *before* the turn is
                # processed: afterwards the discourse state already contains
                # the new turn and the resolution would report the wrong
                # referent.
                _, resolved = self.dialogue_manager.resolve_reference(user_input)
                reference = self._describe_reference(user_input, resolved)

                # Process with dialogue context
                answer, context = self.process_dialogue(user_input, context)
                print(f"\nAssistant: {answer}")

                if reference:
                    print(f"  [Ngữ cảnh: {reference}]")

                intent = context.get('last_intent')
                if intent:
                    print(f"  [Diễn giải: {intent}]")

            except KeyboardInterrupt:
                print("\n\nCảm ơn bạn đã sử dụng Course Assistant!")
                break
            except (EOFError, OSError):
                # The input stream was closed (piped input, CI, ...).
                break
            except Exception as e:
                print(f"\nLỗi: {str(e)}")

    @staticmethod
    def _format_state(state: Dict) -> str:
        """A human readable rendering of the discourse state."""
        if not state or not state.get('turn'):
            return "(chưa có lượt nào)"
        lines = [
            f"lượt: {state.get('turn')}",
            f"intent gần nhất: {state.get('last_intent')}",
        ]
        for slot in ('last_topic', 'last_chapter', 'last_week', 'last_part',
                     'last_assignment', 'last_lo'):
            value = state.get(slot)
            if value:
                lines.append(f"{slot}: {value}")
        lines.append(f"số thực thể đang nổi bật: {state.get('entity_count', 0)}")
        return "\n".join("  " + line for line in lines)

    @staticmethod
    def _describe_reference(user_input: str, resolved: Dict) -> Optional[str]:
        """Describe the reference that was resolved, for the interactive log."""
        if not resolved:
            return None
        inferred = resolved.get('inferred_entities') or {}
        if not inferred:
            return None
        parts = ", ".join(f"{key}={value}" for key, value in sorted(inferred.items()))
        surface = detect_reference_surface(user_input)
        label = f'"{surface}" → ' if surface else ""
        return f"{label}{parts} (conf={resolved.get('confidence', 1.0):.2f})"


# ---------------------------------------------------------------------------
# Demo modes
# ---------------------------------------------------------------------------
def run_pipeline_demo():
    """Demonstrate the full NLP pipeline"""
    assistant = CourseAssistant()

    test_queries = [
        "Môn NLP có bao nhiêu tín chỉ?",
        "Tuần 3 học những gì?",
        "Chương nào học về CFG?",
        "Deadline BTL là khi nào?",
        "Tài liệu về PCFG ở đâu?",
        "Bài tập lớn có những phần nào?",
        "Quy định về sử dụng AI là gì?",
    ]

    print("=" * 70)
    print("COURSE ASSISTANT - FULL PIPELINE DEMO")
    print("=" * 70)

    for query in test_queries:
        print(f"\n{'='*70}")
        print(f"Query: {query}")
        print("-" * 70)

        result = assistant.process_query(query)

        print(f"Normalized: {result['normalized_query']}")
        print(f"Tokens: {result['tokens']}")
        print(f"Parse Result: {result['parse_result']}")
        print(f"Intent: {result['intent']}")
        print(f"Entities: {result['entities']}")
        print(f"Semantic Rep: {result['semantic_rep']}")
        print("-" * 70)
        print(f"Answer: {result['answer']}")


def run_dialogue_demo():
    """Demonstrate the multi-turn dialogue handling"""
    assistant = CourseAssistant()

    print("=" * 70)
    print("COURSE ASSISTANT - DIALOGUE DEMO")
    print("=" * 70)

    context = {}
    for first, second in DEMO_DIALOGUES:
        # Every dialogue starts from a clean discourse state.
        assistant.reset_dialogue()
        context = {}
        for user_input in (first, second):
            answer, context = assistant.process_dialogue(user_input, context)
            print(f"\nUser: {user_input}")
            print(f"Assistant: {answer}")
        print(f"State: {assistant.get_dialogue_state()}")


def run_grammar_demo():
    """Demonstrate grammar and sentence generation"""
    print("\n" + "=" * 70)
    print("GRAMMAR GENERATION DEMO")
    print("=" * 70)

    grammar = CFG()

    print("\nGrammar Rules Sample:")
    print("-" * 40)
    grammar.print_grammar()

    print("\n" + "-" * 40)
    print("Generated Sentences:")
    print("-" * 40)

    sentences = grammar.generate_all_sentences(max_sentences=30)
    for i, sent in enumerate(sentences[:30], 1):
        print(f"{i:3}. {sent}")


def run_parsing_demo():
    """Demonstrate parsing"""
    print("\n" + "=" * 70)
    print("PARSING DEMO")
    print("=" * 70)

    parser = Parser()

    test_sentences = [
        "Môn NLP có bao nhiêu tín chỉ?",
        "Tuần 3 học gì?",
        "Chương 4 nói về gì?",
        "Deadline BTL là khi nào?",
        "Tài liệu về CFG ở đâu?",
    ]

    for sentence in test_sentences:
        print(f"\nInput: {sentence}")
        result = parser.get_parse_result(sentence)
        print(f"Output: {result}")


# ---------------------------------------------------------------------------
# Output artefacts
# ---------------------------------------------------------------------------
def load_analysis_sentences() -> List[str]:
    """
    The sentences analysed in the output artefacts.

    ``input/sentences.txt`` is preferred when it exists; the built-in list
    is the fallback so that the artefacts can always be regenerated.
    """
    input_file = os.path.join(project_root(), 'input', 'sentences.txt')
    if os.path.exists(input_file):
        with open(input_file, 'r', encoding='utf-8') as fh:
            sentences = [
                line.strip() for line in fh
                if line.strip() and not line.strip().startswith('#')
            ]
        if sentences:
            return sentences
    return list(ANALYSIS_SENTENCES)


def write_grammar(output_dir: str) -> None:
    """Artefact 1/9 -- the CFG with its annotations."""
    grammar = CFG()
    with open(os.path.join(output_dir, 'grammar.txt'), 'w', encoding='utf-8') as fh:
        fh.write(grammar.to_string())


def write_samples(output_dir: str) -> None:
    """Artefact 2/9 -- the template questions and the generated sentences."""
    template_sentences = generate_template_sentences()
    grammar_sentences = CFG().generate_all_sentences(max_sentences=10000)

    with open(os.path.join(output_dir, 'samples.txt'), 'w', encoding='utf-8') as fh:
        fh.write("# Template-based sentences (with intent labels)\n")
        for sent, intent in template_sentences:
            fh.write(f"{sent}\t(intent={intent})\n")

        fh.write("\n# Grammar-generated sentences (raw, no intent labels)\n")
        for sent in grammar_sentences:
            fh.write(f"{sent}\n")


def write_parse_results(output_dir: str, sentences: List[str]) -> None:
    """Artefact 3/9 -- the parse trees with an explicit parse-mode label."""
    parser = Parser()
    with open(os.path.join(output_dir, 'parse-results.txt'), 'w', encoding='utf-8') as fh:
        fh.write("PARSE RESULTS\n")
        fh.write("=" * 70 + "\n")
        fh.write("Label: [STRICT] = parsed by the grammar-driven chart parser,\n")
        fh.write("       [FALLBACK] = outside the grammar, matched by the\n")
        fh.write("                    pattern-based fallback,\n")
        fh.write("       [INVALID]  = no tree could be produced.\n")
        fh.write("=" * 70 + "\n\n")

        for sentence in sentences:
            tree, errors = parser.parse(sentence)
            if tree is None:
                label = "[INVALID]"
            elif parser.parse_strict(sentence) is not None:
                label = "[STRICT]"
            else:
                label = "[FALLBACK]"

            fh.write(f"{sentence}\n")
            fh.write(f"{label}\n")
            fh.write(f"{tree if tree is not None else '()'}\n")
            if errors:
                fh.write(f"Errors: {errors}\n")
            fh.write("\n")


def write_semantic(output_dir: str, sentences: List[str]) -> None:
    """Artefact 4/9 -- the semantic representation of every sentence."""
    analyzer = SemanticAnalyzer()
    with open(os.path.join(output_dir, 'semantic.txt'), 'w', encoding='utf-8') as fh:
        fh.write("SEMANTIC REPRESENTATION\n")
        fh.write("=" * 70 + "\n\n")
        for sentence in sentences:
            sem_rep = analyzer.analyze(sentence)
            fh.write(f"Query: {sentence}\n")
            fh.write(f"Intent: {sem_rep.intent.value}\n")
            fh.write(f"Entities: {sem_rep.entities}\n")
            fh.write(f"Logical Form: {sem_rep.to_logical_form()}\n\n")


def write_intent_entity(output_dir: str, sentences: List[str]) -> None:
    """Artefact 5/9 -- the intent / entity table."""
    analyzer = SemanticAnalyzer()
    with open(os.path.join(output_dir, 'intent-entity.txt'), 'w', encoding='utf-8') as fh:
        fh.write("INTENT - ENTITY EXTRACTION\n")
        fh.write("=" * 70 + "\n")
        fh.write(f"{'Query':<48} | {'Intent':<20} | Entities\n")
        fh.write(f"{'-'*48}-+-{'-'*20}-+-{'-'*30}\n")
        for sentence in sentences:
            sem_rep = analyzer.analyze(sentence)
            entities = ", ".join(f"{k}={v}" for k, v in sem_rep.entities.items())
            fh.write(f"{sentence:<48} | {sem_rep.intent.value:<20} | {entities}\n")


def write_query_and_answer(output_dir: str, sentences: List[str]) -> None:
    """Artefacts 6/9 and 7/9 -- the logical query and the answer."""
    assistant = CourseAssistant()
    with open(os.path.join(output_dir, 'query.txt'), 'w', encoding='utf-8') as qf, \
         open(os.path.join(output_dir, 'answer.txt'), 'w', encoding='utf-8') as af:
        qf.write("LOGICAL FORM / KNOWLEDGE BASE QUERY\n")
        qf.write("=" * 70 + "\n\n")
        af.write("ANSWERS\n")
        af.write("=" * 70 + "\n\n")

        for sentence in sentences:
            result = assistant.process_query(sentence)
            intent = result['intent']
            entities = result['entities']
            query = f"{intent}({', '.join(f'{k}={v}' for k, v in entities.items())})"

            qf.write(f"Query: {sentence}\n")
            qf.write(f"Intent Query: {query}\n\n")

            af.write(f"Query: {sentence}\n")
            af.write(f"Intent Query: {query}\n")
            af.write(f"Answer: {result['answer']}\n\n")


def write_dialogue(output_dir: str) -> None:
    """
    Artefact 8/9 -- the multi-turn dialogues.

    Every turn shows the four parts the assignment asks for: the user
    utterance, the discourse context that was used, the interpretation
    (intent + entities + resolved reference) and the answer.

    Each dialogue starts from a **clean** discourse state so that the
    examples are independent of each other.
    """
    with open(os.path.join(output_dir, 'dialogue.txt'), 'w', encoding='utf-8') as fh:
        fh.write("=" * 73 + "\n")
        fh.write("DIALOGUE EXAMPLES - LOCAL DISCOURSE CONTEXT\n")
        fh.write("=" * 73 + "\n")
        fh.write("Mỗi lượt gồm 4 phần: câu hỏi · ngữ cảnh dùng · diễn giải · trả lời.\n")
        fh.write("=" * 73 + "\n")

        for index, (first, second) in enumerate(DEMO_DIALOGUES, start=1):
            fh.write(f"\nDIALOGUE {index:02d}\n")
            fh.write("-" * 73 + "\n")

            # A fresh assistant: every dialogue is independent.
            assistant = CourseAssistant()
            context: Dict = {}

            for turn, user_input in enumerate((first, second), start=1):
                # The state *before* the turn is the context the turn uses.
                state_before = assistant.get_dialogue_state()
                _, resolved = assistant.dialogue_manager.resolve_reference(user_input)
                answer, context = assistant.process_dialogue(user_input, context)
                state_after = assistant.get_dialogue_state()

                entities = context.get("entities", {}) or {}

                fh.write(f"\nTurn {turn}\n")
                fh.write(f"  User      : {user_input}\n")

                # -- part 2: the context that was used -------------------
                fh.write(f"  Context   : {describe_context(state_before)}\n")

                # -- part 3: the interpretation --------------------------
                intent = context.get('last_intent', '?')
                if entities:
                    entity_text = ", ".join(
                        f"{k}={v}" for k, v in sorted(entities.items())
                    )
                else:
                    entity_text = "(không có thực thể)"
                fh.write(f"  Interpret : {intent}({entity_text})\n")

                reference = describe_reference(user_input, resolved)
                if reference:
                    fh.write(f"  Reference : {reference}\n")

                # -- part 4: the answer ---------------------------------
                fh.write(f"  Answer    : {answer}\n")
                fh.write(f"  State     : {describe_state_after(state_after)}\n")

            fh.write("\n" + "-" * 73 + "\n")


def describe_context(state: Dict) -> str:
    """Render the discourse state that a turn relies on."""
    if not state or not state.get('turn'):
        return "(không có - lượt đầu tiên của hội thoại)"
    parts = [f"last_intent={state.get('last_intent')}"]
    for slot in ('last_chapter', 'last_week', 'last_part', 'last_topic',
                 'last_assignment', 'last_lo'):
        value = state.get(slot)
        if value:
            parts.append(f"{slot.replace('last_', '')}={value}")
    return ", ".join(parts)


def describe_state_after(state: Dict) -> str:
    """Render the discourse state after a turn."""
    if not state:
        return "(rỗng)"
    return (
        f"turn={state.get('turn')}, "
        f"last_intent={state.get('last_intent')}, "
        f"entities={state.get('entity_count', 0)}"
    )


# The surface forms that carry a contextual reference, longest first.
REFERENCE_SURFACES = (
    "nội dung này", "phần này", "chương này", "tuần này", "bài này",
    "đề này", "cái này", "chương sau", "tuần sau", "phần sau",
    "tiếp theo", "nó", "hắn", "chúng",
)

# The pronouns of the reference set.
REFERENCE_PRONOUNS = ("nó", "hắn", "chúng")


def detect_reference_surface(user_input: str) -> str:
    """
    The surface form of the contextual reference inside ``user_input``.

    The longest form wins so that ``"phần này"`` is preferred over the
    pronoun ``"nó"``.  An empty string is returned when the question does
    not contain a reference.
    """
    lowered = (user_input or "").lower()
    for surface in REFERENCE_SURFACES:
        if surface in lowered:
            return surface
    return ""


def describe_reference(user_input: str, resolved: Dict) -> str:
    """Render the resolved reference of a turn."""
    if not resolved:
        return ""
    inferred = resolved.get('inferred_entities') or {}
    if not inferred:
        if resolved.get('unresolved_reference'):
            return "không giải được - cần hỏi lại người dùng"
        return ""

    surface = detect_reference_surface(user_input)

    if surface in REFERENCE_PRONOUNS:
        kind = "pronoun"
    elif surface.endswith("sau") or surface == "tiếp theo":
        kind = "next"
    else:
        kind = "definite"

    targets = ", ".join(f"{k}={v}" for k, v in sorted(inferred.items()))
    confidence = resolved.get('confidence', 1.0)
    return (
        f'"{surface}" → {targets} '
        f"(loại: {kind} | nguồn: discourse state | độ tin cậy: {confidence:.2f})"
    )


def write_evaluation(output_dir: str) -> None:
    """Artefact 9/9 -- the evaluation report."""
    from .evaluation import build_full_report

    with open(os.path.join(output_dir, 'evaluation.txt'), 'w', encoding='utf-8') as fh:
        fh.write(build_full_report())


def save_outputs(output_dir: str, seed: int = 42):
    """
    Write the nine artefacts of ``output/``.

    The function is deterministic: running it twice produces byte-identical
    files, which makes the artefacts safe to regenerate before a demo.
    """
    os.makedirs(output_dir, exist_ok=True)
    sentences = load_analysis_sentences()

    print(f"Generating the {len(OUTPUT_FILES)} output artefacts in {output_dir} ...")

    print("  [1/9] grammar.txt")
    write_grammar(output_dir)

    print("  [2/9] samples.txt")
    write_samples(output_dir)

    print("  [3/9] parse-results.txt")
    write_parse_results(output_dir, sentences)

    print("  [4/9] semantic.txt")
    write_semantic(output_dir, sentences)

    print("  [5/9] intent-entity.txt")
    write_intent_entity(output_dir, sentences)

    print("  [6/9] query.txt")
    print("  [7/9] answer.txt")
    write_query_and_answer(output_dir, sentences)

    print("  [8/9] dialogue.txt")
    write_dialogue(output_dir)

    print("  [9/9] evaluation.txt")
    write_evaluation(output_dir)

    print(f"Done. {len(OUTPUT_FILES)} output files written.")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Course Assistant - NLP Assignment')
    parser.add_argument('--mode', choices=['demo', 'interactive', 'generate'], default='demo',
                        help='Run mode: demo, interactive, or generate outputs')
    parser.add_argument('--output', default='output', help='Output directory')

    args = parser.parse_args()

    if args.mode == 'demo':
        run_pipeline_demo()
        run_dialogue_demo()
        run_grammar_demo()
        run_parsing_demo()
    elif args.mode == 'interactive':
        assistant = CourseAssistant()
        assistant.run_interactive()
    elif args.mode == 'generate':
        # The output directory is resolved relative to the project root so
        # that ``python -m src.main --mode generate`` works from anywhere.
        output_dir = args.output
        if not os.path.isabs(output_dir):
            output_dir = os.path.join(project_root(), output_dir)
        save_outputs(output_dir)


if __name__ == "__main__":
    main()
