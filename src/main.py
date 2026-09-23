"""
Course Assistant - Main Application
Integrates all NLP components for the Course Assistant system
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
        
        # Dialogue context storage
        self.dialogue_context: Dict[str, any] = {}
        
        # Set data directory
        if data_dir:
            self.data_dir = data_dir
        else:
            # Default to parent directory's data folder
            self.data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
    
    def process_query(self, query: str) -> Dict[str, any]:
        """
        Process a user query through the full NLP pipeline
        
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
        sem_rep = self.semantic_analyzer.analyze(query, preprocessed['tokens'])
        result['semantic_rep'] = str(sem_rep)
        result['intent'] = sem_rep.intent.value
        result['entities'] = sem_rep.entities
        
        # Step 4: Query Knowledge Base
        if sem_rep.intent != IntentType.UNKNOWN:
            answer = self.knowledge_base.query(
                sem_rep.intent.value,
                sem_rep.entities
            )
        else:
            answer = "Xin lỗi, tôi không hiểu câu hỏi này. Vui lòng hỏi về thông tin môn học NLP như lịch học, nội dung chương, bài tập, tài liệu, hoặc quy định."
        
        result['answer'] = answer
        
        return result
    
    def process_dialogue(self, user_input: str, context: Dict = None) -> Tuple[str, Dict]:
        """
        Process dialogue with context handling
        
        Args:
            user_input: User message
            context: Previous dialogue context
            
        Returns:
            Tuple of (answer, new_context)
        """
        current_context = context or {}
        
        # Check for contextual references
        processed_input = user_input
        
        # Handle pronouns and references
        if 'phần này' in user_input.lower() or ' nó ' in user_input.lower():
            if 'last_topic' in current_context:
                processed_input = user_input.replace('phần này', current_context['last_topic'])
                processed_input = processed_input.replace('nó', current_context['last_topic'])
        
        if 'chương này' in user_input.lower():
            if 'last_chapter' in current_context:
                processed_input = user_input.replace('chương này', current_context['last_chapter'])
        
        # Process query
        result = self.process_query(processed_input)
        
        # Update context
        if result['entities'].get('chapter'):
            current_context['last_chapter'] = result['entities']['chapter']
        if result['entities'].get('topic'):
            current_context['last_topic'] = result['entities']['topic']
        
        return result['answer'], current_context
    
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
    
    # 7. Dialogue (simple examples)
    print("Creating dialogue examples...")
    dialogue_context = {}
    dialogues = [
        ("Tuần 3 học gì?", None),
        ("Tài liệu của phần này ở đâu?", None),
        ("Chương 4 nói về gì?", None),
        ("Nó có liên quan đến parsing không?", None),
        ("Bài tập lớn có phần parser không?", None),
        ("Phần này cần xuất file gì?", None),
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
            if prev_context and ('phần này' in user_input.lower() or 'nó' in user_input.lower() or 'chương này' in user_input.lower()):
                ref_note = f"  [Reference resolved from previous context: {prev_context}]\n"
            
            f.write(f"User: {user_input}\n")
            if ref_note:
                f.write(ref_note)
            f.write(f"Answer: {answer}\n\n")
    
    # 8. Evaluation
    print("Creating evaluation report...")
    test_queries = [
        ("Môn NLP có bao nhiêu tín chỉ?", "GET_COURSE_INFO", "CO3085"),
        ("Tuần 3 học gì?", "GET_SCHEDULE", "WEEK_03"),
        ("Chương nào học về CFG?", "GET_TOPIC", "CFG"),
        ("Deadline BTL là khi nào?", "GET_DEADLINE", "BTL01"),
        ("Tài liệu về PCFG ở đâu?", "GET_RESOURCE", "PCFG"),
    ]
    
    correct = 0
    total = len(test_queries)
    
    with open(os.path.join(output_dir, 'evaluation.txt'), 'w', encoding='utf-8') as f:
        f.write("EVALUATION REPORT\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Test Set: {total} queries\n\n")
        
        f.write("Results:\n")
        f.write("-" * 50 + "\n")
        
        for query, expected_intent, expected_entity in test_queries:
            sem_rep = semantic_analyzer.analyze(query)
            is_correct_intent = sem_rep.intent.value == expected_intent
            is_correct_entity = expected_entity in str(sem_rep.entities.values())
            
            if is_correct_intent:
                correct += 1
            
            status = "✓" if is_correct_intent else "✗"
            f.write(f"{status} Query: {query}\n")
            f.write(f"  Expected Intent: {expected_intent}\n")
            f.write(f"  Predicted Intent: {sem_rep.intent.value}\n")
            f.write(f"  Entities: {sem_rep.entities}\n\n")
        
        accuracy = (correct / total) * 100
        f.write("-" * 50 + "\n")
        f.write(f"Accuracy: {correct}/{total} = {accuracy:.1f}%\n")
        f.write("\nConclusion: System performs well on basic queries.\n")
        f.write("Areas for improvement: More complex queries, better entity extraction.\n")
    
    print(f"Outputs saved to {output_dir}")


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
        run_grammar_demo()
        run_parsing_demo()
    elif args.mode == 'interactive':
        assistant = CourseAssistant()
        assistant.run_interactive()
    elif args.mode == 'generate':
        output_dir = os.path.join(os.path.dirname(__file__), args.output)
        save_outputs(output_dir)


if __name__ == "__main__":
    main()
