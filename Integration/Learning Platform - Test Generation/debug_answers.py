#!/usr/bin/env python3
"""Debug answer comparison"""

import sys
sys.path.insert(0, '/Users/shivenk/Documents/Capstone/Learning Platform - Test Generation')

from question_generator import generate_test, get_pipeline
from evaluation_module import set_pipeline, TestEvaluator

# Generate a test
print("Generating test...")
test_output = generate_test()

# Get the pipeline and set it for evaluation
pipe = get_pipeline()
set_pipeline(pipe)

# Create student info
student_info = {
    'name': 'Test Student',
    'age': '9',
    'grade': 'Grade 3'
}

# Parse the test to see what the correct answers look like
evaluator = TestEvaluator(test_output, student_info, {})
questions_with_answers = evaluator._parse_test_with_answers()

print("\n" + "="*80)
print("PARSED QUESTIONS AND CORRECT ANSWERS:")
print("="*80 + "\n")

for section_name, questions in questions_with_answers.items():
    print(f"\n{section_name}:")
    for idx, q_data in enumerate(questions):
        question_id = f"{section_name}_{idx}"
        print(f"  Question ID: {question_id}")
        print(f"  Question: {q_data['question'][:50]}...")
        print(f"  Correct Answer: '{q_data['correct_answer']}'")
        print(f"  All Choices:")
        for choice in q_data['choices']:
            print(f"    '{choice}'")
        print()

# Now simulate answering with the correct answers
print("\n" + "="*80)
print("SIMULATING STUDENT ANSWERS (all correct):")
print("="*80 + "\n")

answers = {}
for section_name, questions in questions_with_answers.items():
    for idx, q_data in enumerate(questions):
        question_id = f"{section_name}_{idx}"
        correct_ans = q_data['correct_answer']
        answers[question_id] = correct_ans
        print(f"{question_id}: Student answers '{correct_ans}'")

# Now calculate accuracy
print("\n" + "="*80)
print("CALCULATING ACCURACY:")
print("="*80 + "\n")

evaluator2 = TestEvaluator(test_output, student_info, answers)
accuracy = evaluator2.calculate_accuracy()

print(f"Overall Accuracy: {accuracy['overall_accuracy']}%")
print(f"Total Correct: {accuracy['total_correct']}/{accuracy['total_questions']}")

for section_name, stats in accuracy['section_stats'].items():
    print(f"\n{section_name}: {stats['accuracy']}% ({stats['correct']}/{stats['total']})")
    
    # Debug each question
    for q_idx, q_data in enumerate(stats['questions']):
        question_id = f"{section_name}_{q_idx}"
        student_answer = answers.get(question_id, "")
        correct_answer = q_data.get('correct_answer', '')
        is_match = student_answer == correct_answer
        
        print(f"  Q{q_idx+1}:")
        print(f"    Student: '{student_answer}'")
        print(f"    Correct: '{correct_answer}'")
        print(f"    Match: {is_match}")
        print(f"    Student len: {len(student_answer)}, Correct len: {len(correct_answer)}")
        if not is_match:
            print(f"    Byte comparison:")
            print(f"      Student bytes: {student_answer.encode()}")
            print(f"      Correct bytes: {correct_answer.encode()}")
