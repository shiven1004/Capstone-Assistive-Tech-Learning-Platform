from langchain_huggingface import HuggingFacePipeline
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from logger import Logger
import warnings
import json
from datetime import datetime
import torch

warnings.filterwarnings("ignore")

LOG = Logger("Evaluation Logger", log_file_needed=True, log_file_path="Logs/evaluation.log", level='DEV')

# Global pipeline reference (will be set by set_pipeline)
_pipe = None

# Keep the evaluation pipeline on the same device as generation
if torch.backends.mps.is_available():
    DEVICE = torch.device("mps")
elif torch.cuda.is_available():
    DEVICE = torch.device("cuda")
else:
    DEVICE = torch.device("cpu")

def set_pipeline(pipe):
    """Set the shared pipeline to avoid reloading the model"""
    global _pipe
    # Ensure the underlying model is on the selected device to prevent meta/mps mismatch
    if hasattr(pipe, "model"):
        pipe.model.to(DEVICE)
    _pipe = pipe
    LOG.debug(f"Pipeline set for evaluation module on device {DEVICE}")

def _get_pipeline():
    """Get the shared pipeline"""
    if _pipe is None:
        raise RuntimeError("Pipeline not set. Call set_pipeline() first from question_generator context.")
    return _pipe

def create_evaluation_chain():
    """Create LLM chain for evaluation and feedback"""
    template = """Evaluate this student's test performance and provide encouraging feedback.

Student: {student_name}, {student_grade}, Age {student_age}

Test Results (✓=correct, ✗=incorrect):
{questions_and_answers}

Provide brief, supportive feedback with:
1. Overall Assessment (2 sentences)
2. Strengths (2-3 specific points)
3. Areas to Practice (2-3 gentle suggestions)
4. Next Steps (1 encouraging sentence)

Keep it short, positive, and helpful for a student with possible dyslexia/ADHD.

Feedback:"""
    
    prompt = PromptTemplate.from_template(template)
    chain = prompt | HuggingFacePipeline(pipeline=_get_pipeline()) | StrOutputParser()
    return chain


class TestEvaluator:
    """Evaluate student test performance and generate feedback"""
    
    def __init__(self, test_output, student_info, answers):
        """
        Initialize evaluator with test data and student responses
        
        Args:
            test_output: Original test output string
            student_info: Student information dict (name, age, grade)
            answers: Dict of student answers {question_id: selected_answer}
        """
        self.test_output = test_output
        self.student_info = student_info
        self.answers = answers
        self.questions_with_answers = self._parse_test_with_answers()
        self.evaluation_results = {}
    
    def _parse_test_with_answers(self):
        """Parse test output to get questions and extract correct answers"""
        import re
        
        questions_data = {}
        lines = self.test_output.split('\n')
        current_section = None
        current_question = None
        current_choices = []
        correct_answer = None
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Section header
            if line.startswith('===') and 'SECTION' in line:
                match = re.search(r'===\s*(.+?)\s+SECTION', line)
                if match:
                    current_section = match.group(1).strip()
                    if current_section not in questions_data:
                        questions_data[current_section] = []
            
            # Question line
            elif re.match(r'^\d+\.\s+', line) and current_section:
                current_question = re.sub(r'^\d+\.\s+', '', line).strip()
                current_choices = []
                correct_answer = None
            
            # Choice lines
            elif re.match(r'^[a-d]\)', line) and current_question:
                # Check if this choice has the [CORRECT] marker
                if '[CORRECT]' in line:
                    # Remove the marker from the choice for display
                    clean_line = line.replace(' [CORRECT]', '')
                    current_choices.append(clean_line)
                    correct_answer = clean_line
                else:
                    current_choices.append(line)
            
            # Empty line or next question - save current question
            elif (line == "" or re.match(r'^\d+\.', line)) and current_question and len(current_choices) >= 3:
                questions_data[current_section].append({
                    'question': current_question,
                    'choices': current_choices[:4],
                    'correct_answer': correct_answer
                })
                current_question = None
                current_choices = []
        
        return questions_data
    
    def calculate_accuracy(self):
        """Calculate accuracy metrics by section and overall"""
        section_stats = {}
        total_correct = 0
        total_questions = 0
        
        for section_idx, (section_name, questions) in enumerate(self.questions_with_answers.items()):
            section_correct = 0
            section_total = len(questions)
            
            for q_idx, q_data in enumerate(questions):
                question_id = f"{section_name}_{q_idx}"
                student_answer = self.answers.get(question_id, "")
                correct_answer = q_data.get('correct_answer', '')
                
                if student_answer == correct_answer:
                    section_correct += 1
                    total_correct += 1
                
                total_questions += 1
            
            accuracy = (section_correct / section_total * 100) if section_total > 0 else 0
            section_stats[section_name] = {
                'correct': section_correct,
                'total': section_total,
                'accuracy': round(accuracy, 2),
                'questions': questions
            }
        
        overall_accuracy = (total_correct / total_questions * 100) if total_questions > 0 else 0
        
        return {
            'section_stats': section_stats,
            'total_correct': total_correct,
            'total_questions': total_questions,
            'overall_accuracy': round(overall_accuracy, 2)
        }
    
    def analyze_patterns(self):
        """Analyze answer patterns for dyslexia and ADHD indicators"""
        accuracy = self.calculate_accuracy()
        section_stats = accuracy['section_stats']
        
        patterns = {
            'completed_questions': len(self.answers),
            'skipped_questions': accuracy['total_questions'] - len(self.answers),
            'section_performance': {},
            'phonological_awareness_score': 0,
            'consistency': 'Unknown',
            'potential_issues': []
        }
        
        # Analyze each section
        for section_name, stats in section_stats.items():
            section_acc = stats['accuracy']
            patterns['section_performance'][section_name] = {
                'accuracy': section_acc,
                'correct': stats['correct'],
                'total': stats['total']
            }
            
            # Track phonological awareness specifically
            if 'PHONOLOGICAL' in section_name.upper():
                patterns['phonological_awareness_score'] = section_acc
        
        # Check for attention/pace indicators (gentle wording)
        if patterns['skipped_questions'] > 2:
            patterns['potential_issues'].append('Some questions were left unanswered. Let’s try shorter sessions and quick breaks to keep focus comfortable.')
        
        # Check for phonological awareness (gentle wording)
        if patterns['phonological_awareness_score'] < 50:
            patterns['potential_issues'].append('Phonological awareness needs more practice. Try light sound games and blending activities together.')
        
        # Check consistency - if performance varies greatly
        accuracies = [stats['accuracy'] for stats in section_stats.values()]
        if max(accuracies) - min(accuracies) > 40:
            patterns['potential_issues'].append('Performance varies across subjects. Let’s focus on one subject at a time with small wins.')
            patterns['consistency'] = 'Inconsistent'
        else:
            patterns['consistency'] = 'Consistent'
        
        return patterns
    
    def generate_llm_feedback(self):
        """Generate detailed LLM-based feedback by having the LLM evaluate actual test answers"""
        accuracy = self.calculate_accuracy()
        
        # Format questions and answers in a CONCISE format (too much text causes LLM to return empty)
        questions_and_answers_text = ""
        question_num = 1
        
        for section_name, stats in accuracy['section_stats'].items():
            questions_and_answers_text += f"\n{section_name}:\n"
            
            for q_idx, q_data in enumerate(stats['questions']):
                question_id = f"{section_name}_{q_idx}"
                student_answer = self.answers.get(question_id, "Not answered")
                correct_answer = q_data.get('correct_answer', 'Unknown')
                
                # Check if answer is correct
                is_correct = student_answer == correct_answer
                result = "✓" if is_correct else "✗"
                
                # Concise format: Q#. Question? → Student: answer [✓/✗]
                questions_and_answers_text += f"{question_num}. {q_data['question']} → Student: {student_answer} [{result}]\n"
                
                question_num += 1
        
        LOG.debug(f"Formatted {question_num-1} questions for LLM evaluation. Text length: {len(questions_and_answers_text)}")
        
        # Create evaluation prompt with Q&A data
        chain = create_evaluation_chain()
        try:
            feedback = chain.invoke({
                'student_name': self.student_info['name'],
                'student_grade': self.student_info['grade'],
                'student_age': self.student_info['age'],
                'questions_and_answers': questions_and_answers_text
            })
            LOG.debug(f"LLM feedback generated. Length: {len(feedback) if feedback else 0}")
            if not feedback or len(feedback.strip()) == 0:
                LOG.warning("LLM returned empty feedback - using fallback")
                # Generate basic feedback based on metrics
                patterns = self.analyze_patterns()
                feedback = f"""**Overall Assessment:**
Great job completing the test, {self.student_info['name']}! You got {accuracy['overall_accuracy']}% correct ({accuracy['total_correct']} out of {accuracy['total_questions']} questions).

**Strengths:**
- You completed {patterns['completed_questions']} questions
- Your consistency level is: {patterns['consistency']}
"""
                # Add section-specific strengths
                for section_name, stats in accuracy['section_stats'].items():
                    if stats['accuracy'] >= 60:
                        feedback += f"- Strong performance in {section_name}: {stats['accuracy']}%\n"
                
                feedback += "\n**Areas for Growth:**\n"
                for section_name, stats in accuracy['section_stats'].items():
                    if stats['accuracy'] < 60:
                        feedback += f"- {section_name} could use more practice ({stats['accuracy']}%)\n"
                
                feedback += "\n**Recommendations:**\n"
                if patterns['phonological_awareness_score'] < 60:
                    feedback += "- Practice phonological awareness with word games and rhyming activities\n"
                feedback += "- Take breaks during longer tests\n- Review questions carefully before answering\n"
                
                feedback += "\n**Next Steps:**\nKeep practicing! Focus on the areas that need improvement, and celebrate your strengths!"
                
        except Exception as e:
            LOG.error(f"LLM feedback generation failed: {type(e).__name__}: {str(e)}", exc_info=True)
            feedback = f"Unable to generate AI feedback at this time. Error: {str(e)}"
        
        return feedback
    
    def generate_detailed_report(self):
        """Generate comprehensive evaluation report"""
        accuracy = self.calculate_accuracy()
        patterns = self.analyze_patterns()
        
        # Generate LLM feedback
        print("🔄 Generating personalized feedback...")
        llm_feedback = self.generate_llm_feedback()
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'student_info': self.student_info,
            'performance_metrics': {
                'overall_accuracy': accuracy['overall_accuracy'],
                'total_correct': accuracy['total_correct'],
                'total_questions': accuracy['total_questions'],
                'section_performance': accuracy['section_stats']
            },
            'pattern_analysis': patterns,
            'llm_feedback': llm_feedback,
            'section_details': {}
        }
        
        # Add section-wise details
        for section_name, stats in accuracy['section_stats'].items():
            report['section_details'][section_name] = {
                'accuracy': stats['accuracy'],
                'correct': stats['correct'],
                'total': stats['total'],
                'questions': [
                    {
                        'question': q['question'],
                        'student_answer': self.answers.get(f"{section_name}_{idx}", "Not answered"),
                        'correct_answer': q['correct_answer'],
                        'is_correct': self.answers.get(f"{section_name}_{idx}") == q['correct_answer']
                    }
                    for idx, q in enumerate(stats['questions'])
                ]
            }
        
        self.evaluation_results = report
        return report
    
    def format_report_for_display(self):
        """Format report for user-friendly display"""
        if not self.evaluation_results:
            self.generate_detailed_report()
        
        report = self.evaluation_results
        
        perf = report['performance_metrics']
        display_lines = []
        display_lines.append("📊 Test Evaluation Report")
        display_lines.append("")
        display_lines.append("👤 Student")
        display_lines.append(f"- Name: {report['student_info']['name']}")
        display_lines.append(f"- Grade: {report['student_info']['grade']}")
        display_lines.append(f"- Age: {report['student_info']['age']}")
        display_lines.append("")
        display_lines.append("📈 Overall Performance")
        display_lines.append(f"- Accuracy: {perf['overall_accuracy']}% ({perf['total_correct']}/{perf['total_questions']} correct)")
        display_lines.append("")
        display_lines.append("📚 Section Performance")
        for section, stats in perf['section_performance'].items():
            display_lines.append(f"- {section}: {stats['accuracy']}% ({stats['correct']}/{stats['total']})")
        display_lines.append("")
        display_lines.append("🤖 AI-Powered Evaluation & Personalized Feedback")
        display_lines.append("")
        display_lines.append(report['llm_feedback'])
        display_lines.append("")
        return "\n".join(display_lines)
    
    def export_report_json(self, filename=None):
        """Export report as JSON"""
        if not self.evaluation_results:
            self.generate_detailed_report()
        
        if filename is None:
            filename = f"evaluation_{self.student_info['name'].replace(' ', '_')}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.evaluation_results, f, indent=2, ensure_ascii=False)
        
        LOG.debug(f"Report exported to {filename}")
        return filename


def evaluate_test(test_output, student_info, answers):
    """
    Main function to evaluate test performance
    
    Args:
        test_output: Original test output string
        student_info: Dict with student info {name, age, grade}
        answers: Dict of answers {question_id: selected_answer}
    
    Returns:
        Formatted evaluation report string
    """
    evaluator = TestEvaluator(test_output, student_info, answers)
    evaluator.generate_detailed_report()
    return evaluator.format_report_for_display()


def get_evaluation_object(test_output, student_info, answers):
    """
    Get TestEvaluator object for programmatic access
    
    Returns:
        TestEvaluator object with all methods available
    """
    return TestEvaluator(test_output, student_info, answers)
