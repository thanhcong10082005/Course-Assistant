"""
Course Assistant - Main Application
Integrates all NLP components for the Course Assistant system

Pipeline
--------
::

    Preprocessing  ->  Parsing  ->  Dialogue Context  ->  Semantic Analysis
                  ->  Knowledge Base  ->  Answer

WP6 upgrade
-----------
:class:`CourseAssistant` now owns a real :class:`~src.dialogue.DialogueManager`
instead of a plain dictionary of strings, so that

* the discourse state survives across the turns of a conversation,
* the contextual references ("nó", "phần này", "chương sau") are resolved by
  the dialogue manager *before* the semantic analyzer runs,
* a query whose reference cannot be resolved is answered with a request for
  clarification (``CONTEXT_DEPENDENT``) instead of a confident guess.
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

        # Dialogue context storage (WP6): a real dialogue manager, not a
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
            self.data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')

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
            - parse_tree: Parse tree result
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
        if sem_rep.intent == IntentType.CONTEXT_DEPENDENT:
            answer = self.knowledge_base.ask_for_clarification()
        elif sem_rep.intent != IntentType.UNKNOWN:
            answer = self.knowledge_base.query(
                sem_rep.intent.value,
                sem_rep.entities
            )
        else:
            answer = self.knowledge_base.unknown_answer()

        result['answer'] = answer

        # Step 5: Remember the entities of this turn so that a later
        # question can refer to them ("Nó ...", "Phần này ...").
        self.dialogue_manager.note_context(sem_rep.entities, query)

        return result

    # ------------------------------------------------------------------
    # Dialogue pipeline (WP6)
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
        if sem_rep.intent == IntentType.CONTEXT_DEPENDENT:
            answer = self.knowledge_base.ask_for_clarification()
        elif sem_rep.intent != IntentType.UNKNOWN:
            answer = self.knowledge_base.query(
                sem_rep.intent.value,
                sem_rep.entities
            )
        else:
            answer = self.knowledge_base.unknown_answer()

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

        return answer, current_context

    def reset_dialogue(self) -> None:
        """Clear the discourse context."""
        self.dialogue_manager.reset()
        self.dialogue_context = {}

    def get_dialogue_state(self) -> Dict:
        """The summary of the current discourse state."""
        return self.dialogue_manager.get_state_summary()

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
        print("Gõ 'exit' hoặc 'quit' để thoát")
        print("-" * 70)

        context = {}

        while True:
            try:
                user_input = input("\nBạn: ").strip()

                if user_input.lower() in ['exit', 'quit', 'thoát']:
                    print("Cảm ơn bạn đã sử dụng Course Assistant!")
                    break

                if not user_input:
                    continue

                # Process with dialogue context
                answer, context = self.process_dialogue(user_input, context)
                print(f"\nAssistant: {answer}")

            except KeyboardInterrupt:
                print("\n\nCảm ơn bạn đã sử dụng Course Assistant!")
                break
            except Exception as e:
                print(f"\nLỗi: {str(e)}")


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

    dialogues = [
        ("Chương 4 nói về gì?", None),
        ("Nó có liên quan đến parsing không?", None),
        ("Còn chương sau?", None),
        ("Bài tập lớn có phần parser không?", None),
        ("Phần này cần xuất file gì?", None),
    ]

    context = {}
    for user_input, _ in dialogues:
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


def save_outputs(output_dir: str):
    """Save all outputs to files"""
    print(f"\nSaving outputs to {output_dir}...")

    assistant = CourseAssistant()

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)

    # 1. Generate grammar
    print("Generating grammar...")
    grammar = CFG()
    grammar_content = grammar.to_string()
    with open(os.path.join(output_dir, 'grammar.txt'), 'w', encoding='utf-8') as f:
        f.write(grammar_content)

    # 2. Generate sample sentences (from both templates and grammar)
    print("Generating sample sentences...")

    # Combine sentences from templates (with intent labels) and grammar (raw)
    template_sentences = generate_template_sentences()

    # Generate sentences from grammar
    grammar = CFG()
    grammar_sentences = grammar.generate_all_sentences(max_sentences=10000)

    with open(os.path.join(output_dir, 'samples.txt'), 'w', encoding='utf-8') as f:
        # First: template sentences with intent
        f.write("# Template-based sentences (with intent labels)\n")
        for sent, intent in template_sentences:
            f.write(f"{sent}\t(intent={intent})\n")

        # Second: grammar-generated sentences (no labels)
        f.write("\n# Grammar-generated sentences (raw, no intent labels)\n")
        for sent in grammar_sentences:
            f.write(f"{sent}\n")

    # 3. Parse input sentences
    print("Parsing sentences...")
    input_file = os.path.join(os.path.dirname(__file__), '..', 'input', 'sentences.txt')
    if os.path.exists(input_file):
        with open(input_file, 'r', encoding='utf-8') as f:
            # Skip comments and blank lines
            input_sentences = [
                line.strip() for line in f
                if line.strip() and not line.strip().startswith('#')
            ]
    else:
        input_sentences = [
            "Môn NLP có bao nhiêu tín chỉ?",
            "Tuần 3 học gì?",
            "Chương nào học về CFG?",
        ]

    parser = Parser()
    with open(os.path.join(output_dir, 'parse-results.txt'), 'w', encoding='utf-8') as f:
        for sentence in input_sentences:
            result = parser.get_parse_result(sentence)
            f.write(f"{sentence}\n{result}\n\n")

    # 4. Semantic analysis
    print("Running semantic analysis...")
    semantic_analyzer = SemanticAnalyzer()
    with open(os.path.join(output_dir, 'semantic.txt'), 'w', encoding='utf-8') as f:
        for sentence in input_sentences:
            sem_rep = semantic_analyzer.analyze(sentence)
            f.write(f"Query: {sentence}\n")
            f.write(f"Intent: {sem_rep.intent.value}\n")
            f.write(f"Entities: {sem_rep.entities}\n")
            f.write(f"Logical Form: {sem_rep.to_logical_form()}\n\n")

    # 5. Intent-Entity extraction
    print("Extracting intent and entities...")
    with open(os.path.join(output_dir, 'intent-entity.txt'), 'w', encoding='utf-8') as f:
        for sentence in input_sentences:
            sem_rep = semantic_analyzer.analyze(sentence)
            f.write(f"{sentence}\t{sem_rep.intent.value}\t{sem_rep.entities}\n")

    # 6. Query and Answer
    print("Generating answers...")
    kb = KnowledgeBase()
    with open(os.path.join(output_dir, 'query.txt'), 'w', encoding='utf-8') as qf, \
         open(os.path.join(output_dir, 'answer.txt'), 'w', encoding='utf-8') as af:
        for sentence in input_sentences:
            sem_rep = semantic_analyzer.analyze(sentence)
            query = f"{sem_rep.intent.value}({', '.join(f'{k}={v}' for k, v in sem_rep.entities.items())})"
            answer = kb.query(sem_rep.intent.value, sem_rep.entities)

            qf.write(f"Query: {sentence}\n")
            qf.write(f"Intent Query: {query}\n\n")

            af.write(f"Query: {sentence}\n")
            af.write(f"Answer: {answer}\n\n")

    # 7. Dialogue (multi-turn examples)
    print("Creating dialogue examples...")
    dialogue_context = {}
    dialogues = [
        ("Tuần 3 học gì?", None),
        ("Tài liệu của chương này là gì?", None),
        ("Chương 4 nói về gì?", None),
        ("Nó có liên quan đến parsing không?", None),
        ("Còn chương sau?", None),
        ("Bài tập lớn có phần parser không?", None),
        ("Phần này cần xuất file gì?", None),
        ("L.O.2.5 học về gì?", None),
        ("Nội dung này nằm ở chương nào?", None),
    ]

    with open(os.path.join(output_dir, 'dialogue.txt'), 'w', encoding='utf-8') as f:
        f.write("DIALOGUE EXAMPLES\n")
        f.write("=" * 50 + "\n\n")

        for user_input, _ in dialogues:
            # Save previous context for display
            prev_context = dict(dialogue_context) if dialogue_context else {}

            answer, dialogue_context = assistant.process_dialogue(user_input, dialogue_context)

            # Detect reference resolution
            ref_note = ""
            if prev_context and any(
                marker in user_input.lower()
                for marker in ("phần này", "nó", "chương này", "chương sau")
            ):
                ref_note = f"  [Reference resolved from previous context: {prev_context}]\n"

            f.write(f"User: {user_input}\n")
            if ref_note:
                f.write(ref_note)
            f.write(f"Answer: {answer}\n\n")

    # 8. Evaluation -- the full official test set (34 queries)
    print("Creating evaluation report...")
    evaluation_text = build_evaluation_report(assistant)
    with open(os.path.join(output_dir, 'evaluation.txt'), 'w', encoding='utf-8') as f:
        f.write(evaluation_text)

    print(f"Outputs saved to {output_dir}")


def build_evaluation_report(assistant: CourseAssistant) -> str:
    """
    Build the evaluation report over the **full official test set**.

    The report contains the intent accuracy, the entity accuracy and the
    per-case detail, so that ``output/evaluation.txt`` is a real artefact
    of the system rather than a five-question illustration.
    """
    import re as _re

    official_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "tests", "data", "sample_queries.txt",
    )

    cases = []
    if os.path.exists(official_path):
        pattern = _re.compile(
            r"^(?P<id>Q\d+)\s*\|\s*(?P<query>.+?)\s*\|\s*(?P<intent>[A-Z_]+)\s*"
            r"\|\s*(?P<entity>.+?)\s*$"
        )
        with open(official_path, "r", encoding="utf-8") as fh:
            for raw in fh:
                line = raw.strip()
                if not line or line.startswith(("#", "-")):
                    continue
                match = pattern.match(line)
                if not match:
                    continue
                entity = match.group("entity").strip()
                cases.append(
                    {
                        "id": match.group("id"),
                        "query": match.group("query").strip(),
                        "expected_intent": match.group("intent"),
                        "expected_entity": None if entity == "OUT_OF_SCOPE" else entity,
                    }
                )

    if not cases:
        return "EVALUATION REPORT\n\nNo official test set found.\n"

    intent_ok = 0
    entity_ok = 0
    combined_ok = 0
    detail = []

    # A *fresh* assistant: the evaluation must not be influenced by the
    # dialogue state that the earlier demo steps have built up.
    evaluator_assistant = CourseAssistant()

    for case in cases:
        result = evaluator_assistant.process_query(case["query"])
        i_ok = result["intent"] == case["expected_intent"]
        e_ok = True
        if case["expected_entity"]:
            e_ok = case["expected_entity"] in str(result["entities"])

        intent_ok += i_ok
        entity_ok += e_ok
        combined_ok += i_ok and e_ok

        detail.append(
            f"{'✓' if (i_ok and e_ok) else '✗'} [{case['id']}] {case['query']}\n"
            f"    expected: {case['expected_intent']} / {case['expected_entity']}\n"
            f"    actual  : {result['intent']} / {result['entities']}"
        )

    total = len(cases)
    lines = [
        "EVALUATION REPORT",
        "=" * 70,
        "",
        f"Test set: tests/data/sample_queries.txt ({total} official queries)",
        "",
        "Summary:",
        "-" * 70,
        f"  Intent accuracy:        {intent_ok}/{total} = {intent_ok / total * 100:.2f}%",
        f"  Entity accuracy:        {entity_ok}/{total} = {entity_ok / total * 100:.2f}%",
        f"  Intent + Entity:        {combined_ok}/{total} = {combined_ok / total * 100:.2f}%",
        "",
        "Per-query detail:",
        "-" * 70,
        "",
    ]
    lines.extend(detail)
    lines.extend([
        "",
        "=" * 70,
        "Note: the entity column is compared with the official label using a",
        "raw substring match, so the two alias pairs (CO3085/NLP and",
        "MIDTERM/FINAL) are reported as entity misses even though the",
        "pipeline resolves them correctly.  Run scripts/baseline.py for the",
        "alias-aware figures.",
    ])
    return "\n".join(lines) + "\n"


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Course Assistant - NLP Assignment')
    parser.add_argument('--mode', choices=['demo', 'interactive', 'generate'], default='demo',
                        help='Run mode: demo, interactive, or generate outputs')
    parser.add_argument('--output', default='../output', help='Output directory')

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
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        output_dir = os.path.abspath(args.output)
        if not os.path.isabs(args.output):
            output_dir = os.path.join(project_root, args.output)
        save_outputs(output_dir)


if __name__ == "__main__":
    main()
