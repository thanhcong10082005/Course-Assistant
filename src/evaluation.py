"""
Evaluation module for Course Assistant
Provides metrics and analysis for system performance
"""

from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass, field
import json


@dataclass
class TestCase:
    """Represents a test case for evaluation"""
    query: str
    expected_intent: str
    expected_entity: Optional[str] = None
    expected_answer_contains: Optional[List[str]] = None
    category: str = "general"  # general, out_of_scope, context_dependent
    is_out_of_scope: bool = False


@dataclass
class EvaluationResult:
    """Result of evaluating a single test case"""
    test_case: TestCase
    predicted_intent: str
    predicted_entities: Dict[str, Any]
    intent_correct: bool
    entity_correct: bool
    answer_correct: bool = False
    error_type: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class EvaluationReport:
    """Overall evaluation report"""
    total_tests: int = 0
    intent_correct: int = 0
    entity_correct: int = 0
    answer_correct: int = 0
    out_of_scope_correct: int = 0
    results: List[EvaluationResult] = field(default_factory=list)
    
    @property
    def intent_accuracy(self) -> float:
        return self.intent_correct / self.total_tests * 100 if self.total_tests > 0 else 0
    
    @property
    def entity_accuracy(self) -> float:
        return self.entity_correct / self.total_tests * 100 if self.total_tests > 0 else 0
    
    @property
    def answer_accuracy(self) -> float:
        return self.answer_correct / self.total_tests * 100 if self.total_tests > 0 else 0
    
    @property
    def out_of_scope_accuracy(self) -> float:
        total_out_of_scope = sum(1 for r in self.results if r.test_case.is_out_of_scope)
        if total_out_of_scope == 0:
            return 0
        correct = sum(1 for r in self.results if r.test_case.is_out_of_scope and r.predicted_intent == "UNKNOWN")
        return correct / total_out_of_scope * 100


class Evaluator:
    """
    Evaluates Course Assistant system performance
    """
    
    def __init__(self, course_assistant=None):
        self.course_assistant = course_assistant
        self.test_cases: List[TestCase] = []
        self.report: Optional[EvaluationReport] = None
    
    def load_test_cases(self, test_cases: List[Dict]):
        """Load test cases from dictionary format"""
        self.test_cases = [
            TestCase(
                query=tc['query'],
                expected_intent=tc.get('expected_intent', 'UNKNOWN'),
                expected_entity=tc.get('expected_entity'),
                expected_answer_contains=tc.get('answer_contains'),
                category=tc.get('category', 'general'),
                is_out_of_scope=tc.get('is_out_of_scope', False)
            )
            for tc in test_cases
        ]
    
    def load_test_cases_from_file(self, filepath: str):
        """Load test cases from file"""
        # Parse sample_queries.txt format
        test_cases = []
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                parts = line.split('|')
                if len(parts) >= 3:
                    test_cases.append({
                        'query': parts[1].strip(),
                        'expected_intent': parts[2].strip(),
                        'expected_entity': parts[3].strip() if len(parts) > 3 else None,
                        'is_out_of_scope': parts[2].strip() == 'UNKNOWN'
                    })
        
        self.load_test_cases(test_cases)
    
    def evaluate(self, assistant=None) -> EvaluationReport:
        """
        Evaluate system on all test cases
        
        Args:
            assistant: CourseAssistant instance (optional, uses self.course_assistant if None)
            
        Returns:
            EvaluationReport with results
        """
        if assistant:
            self.course_assistant = assistant
        
        if not self.course_assistant:
            raise ValueError("No CourseAssistant instance provided")
        
        report = EvaluationReport(total_tests=len(self.test_cases))
        
        for test_case in self.test_cases:
            # Process query
            result = self.course_assistant.process_query(test_case.query)
            
            # Check intent
            intent_correct = result['intent'] == test_case.expected_intent
            
            # Check entity
            entity_correct = True
            if test_case.expected_entity:
                entity_correct = test_case.expected_entity in str(result['entities'])
            
            # Check answer (if specified)
            answer_correct = False
            if test_case.expected_answer_contains:
                answer_correct = all(
                    keyword.lower() in result['answer'].lower() 
                    for keyword in test_case.expected_answer_contains
                )
            elif test_case.is_out_of_scope:
                # For out-of-scope, check if UNKNOWN intent or "not found" message
                answer_correct = result['intent'] == 'UNKNOWN' or 'không tìm thấy' in result['answer'].lower()
            
            # Determine error type
            error_type = None
            error_message = None
            if not intent_correct:
                error_type = "intent_error"
                error_message = f"Expected {test_case.expected_intent}, got {result['intent']}"
            elif not entity_correct:
                error_type = "entity_error"
                error_message = f"Missing expected entity {test_case.expected_entity}"
            
            # Create result
            eval_result = EvaluationResult(
                test_case=test_case,
                predicted_intent=result['intent'],
                predicted_entities=result['entities'],
                intent_correct=intent_correct,
                entity_correct=entity_correct,
                answer_correct=answer_correct,
                error_type=error_type,
                error_message=error_message
            )
            
            report.results.append(eval_result)
            
            # Update counts
            if intent_correct:
                report.intent_correct += 1
            if entity_correct:
                report.entity_correct += 1
            if answer_correct:
                report.answer_correct += 1
            if test_case.is_out_of_scope and result['intent'] == 'UNKNOWN':
                report.out_of_scope_correct += 1
        
        self.report = report
        return report
    
    def generate_report(self) -> str:
        """Generate evaluation report as string"""
        if not self.report:
            return "No evaluation results. Run evaluate() first."
        
        r = self.report
        lines = []
        
        lines.append("=" * 70)
        lines.append("COURSE ASSISTANT EVALUATION REPORT")
        lines.append("=" * 70)
        
        lines.append(f"\nTest Set Statistics:")
        lines.append(f"  Total test cases: {r.total_tests}")
        lines.append(f"  In-scope tests: {sum(1 for tc in self.test_cases if not tc.is_out_of_scope)}")
        lines.append(f"  Out-of-scope tests: {sum(1 for tc in self.test_cases if tc.is_out_of_scope)}")
        
        lines.append(f"\nAccuracy Metrics:")
        lines.append(f"  Intent Accuracy: {r.intent_accuracy:.2f}% ({r.intent_correct}/{r.total_tests})")
        lines.append(f"  Entity Accuracy: {r.entity_accuracy:.2f}% ({r.entity_correct}/{r.total_tests})")
        lines.append(f"  Answer Accuracy: {r.answer_accuracy:.2f}% ({r.answer_correct}/{r.total_tests})")
        lines.append(f"  Out-of-Scope Detection: {r.out_of_scope_accuracy:.2f}%")
        
        # Per-intent accuracy
        lines.append(f"\nPer-Intent Performance:")
        intent_stats = {}
        for result in r.results:
            intent = result.test_case.expected_intent
            if intent not in intent_stats:
                intent_stats[intent] = {'correct': 0, 'total': 0}
            intent_stats[intent]['total'] += 1
            if result.intent_correct:
                intent_stats[intent]['correct'] += 1
        
        lines.append(f"  {'Intent':<25} {'Correct':<10} {'Total':<10} {'Accuracy':<10}")
        lines.append(f"  {'-'*55}")
        for intent, stats in sorted(intent_stats.items()):
            acc = stats['correct'] / stats['total'] * 100 if stats['total'] > 0 else 0
            lines.append(f"  {intent:<25} {stats['correct']:<10} {stats['total']:<10} {acc:.1f}%")
        
        # Error analysis
        lines.append(f"\nError Analysis:")
        error_counts = {}
        for result in r.results:
            if result.error_type:
                error_counts[result.error_type] = error_counts.get(result.error_type, 0) + 1
        
        if error_counts:
            lines.append(f"  Error Type Distribution:")
            for error_type, count in sorted(error_counts.items(), key=lambda x: -x[1]):
                lines.append(f"    {error_type}: {count} ({count/len(r.results)*100:.1f}%)")
        else:
            lines.append(f"  No errors detected.")
        
        # Example errors
        error_results = [r for r in r.results if r.error_type]
        if error_results:
            lines.append(f"\nExample Errors:")
            for result in error_results[:5]:
                lines.append(f"  Query: {result.test_case.query}")
                lines.append(f"  Expected: {result.test_case.expected_intent}")
                lines.append(f"  Predicted: {result.predicted_intent}")
                lines.append(f"  Error: {result.error_message}")
                lines.append("")
        
        # Limitations
        lines.append(f"\nLimitations:")
        lines.append(f"  - Rule-based intent classification has limited coverage")
        lines.append(f"  - Cannot handle complex multi-intent queries")
        lines.append(f"  - Vietnamese NLP normalization needs improvement")
        lines.append(f"  - Out-of-scope detection is conservative")
        
        lines.append("\n" + "=" * 70)
        
        return "\n".join(lines)
    
    def save_report(self, filepath: str):
        """Save evaluation report to file"""
        report_text = self.generate_report()
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report_text)
    
    def to_dict(self) -> Dict:
        """Convert report to dictionary"""
        if not self.report:
            return {}
        
        r = self.report
        return {
            'total_tests': r.total_tests,
            'intent_accuracy': r.intent_accuracy,
            'entity_accuracy': r.entity_accuracy,
            'answer_accuracy': r.answer_accuracy,
            'out_of_scope_accuracy': r.out_of_scope_accuracy,
            'results': [
                {
                    'query': result.test_case.query,
                    'expected_intent': result.test_case.expected_intent,
                    'predicted_intent': result.predicted_intent,
                    'intent_correct': result.intent_correct,
                    'error_type': result.error_type
                }
                for result in r.results
            ]
        }


# Standard test cases for Course Assistant
DEFAULT_TEST_CASES = [
    # Course Info
    {"query": "Môn NLP có bao nhiêu tín chỉ?", "expected_intent": "GET_COURSE_INFO", "expected_entity": "NLP"},
    {"query": "CO3085 có mấy tín chỉ?", "expected_intent": "GET_COURSE_INFO", "expected_entity": "CO3085"},
    {"query": "Midterm kéo dài bao lâu?", "expected_intent": "GET_COURSE_INFO", "expected_entity": "midterm"},
    {"query": "Final có thời lượng bao nhiêu?", "expected_intent": "GET_COURSE_INFO", "expected_entity": "final"},
    
    # Schedule
    {"query": "Tuần 3 học gì?", "expected_intent": "GET_SCHEDULE", "expected_entity": "WEEK_03"},
    {"query": "Hôm nay học lịch nào?", "expected_intent": "GET_SCHEDULE"},
    
    # Topic
    {"query": "Chương 4 nói về gì?", "expected_intent": "GET_TOPIC", "expected_entity": "CH04"},
    {"query": "Chương nào học về CFG?", "expected_intent": "GET_TOPIC", "expected_entity": "CFG"},
    {"query": "CFG nằm ở chương nào?", "expected_intent": "GET_TOPIC", "expected_entity": "CFG"},
    
    # Assignment
    {"query": "Bài tập lớn yêu cầu gì?", "expected_intent": "GET_ASSIGNMENT", "expected_entity": "BTL01"},
    {"query": "BTL gồm những phần nào?", "expected_intent": "GET_ASSIGNMENT"},
    
    # Deadline
    {"query": "Deadline BTL là khi nào?", "expected_intent": "GET_DEADLINE", "expected_entity": "BTL01"},
    {"query": "Thời hạn nộp bài tập lớn?", "expected_intent": "GET_DEADLINE"},
    
    # Resource
    {"query": "Tài liệu về CFG ở đâu?", "expected_intent": "GET_RESOURCE", "expected_entity": "CFG"},
    {"query": "Có sách tham khảo nào không?", "expected_intent": "GET_RESOURCE"},
    
    # Rule
    {"query": "Có được sử dụng LLM không?", "expected_intent": "GET_RULE"},
    {"query": "Quy định về AI là gì?", "expected_intent": "GET_RULE"},
    
    # Out of scope
    {"query": "Hôm nay thời tiết thế nào?", "expected_intent": "UNKNOWN", "is_out_of_scope": True},
    {"query": "Ai là tổng thống Mỹ?", "expected_intent": "UNKNOWN", "is_out_of_scope": True},
    {"query": "Giải bài toán này giúp tôi", "expected_intent": "UNKNOWN", "is_out_of_scope": True},
]


def run_evaluation():
    """Run evaluation with default test cases"""
    from .main import CourseAssistant
    
    print("Running Course Assistant Evaluation...")
    print("=" * 60)
    
    # Initialize system
    assistant = CourseAssistant()
    
    # Create evaluator
    evaluator = Evaluator(assistant)
    evaluator.load_test_cases(DEFAULT_TEST_CASES)
    
    # Run evaluation
    report = evaluator.evaluate()
    
    # Print report (avoid Unicode encoding issues on Windows)
    report_text = evaluator.generate_report()
    try:
        print(report_text)
    except UnicodeEncodeError:
        # Fall back to ASCII-safe output
        print(report_text.encode('ascii', 'replace').decode('ascii'))
    
    # Save to file
    evaluator.save_report("output/evaluation.txt")
    print("\nReport saved to output/evaluation.txt")


if __name__ == "__main__":
    run_evaluation()
