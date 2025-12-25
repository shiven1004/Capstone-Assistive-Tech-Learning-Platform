import streamlit as st
import re
from question_generator import generate_test
from evaluation_module import evaluate_test

st.set_page_config(page_title="Learning Platform - Test Generator", layout="wide")

def show_registration_page():
    """Show student registration form"""
    st.title("🎓 Learning Platform - Student Registration")
    st.markdown("### Please fill in your information to get started")
    
    with st.form("registration_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Student Name *", placeholder="Enter your full name")
            grade = st.selectbox("Grade Level *", 
                               options=["", "Grade 1", "Grade 2", "Grade 3", "Grade 4", "Grade 5"],
                               index=0)
        
        with col2:
            age = st.number_input("Age *", min_value=4, max_value=18, value=None, placeholder="Enter age")
        
        st.markdown("*Required fields")
        
        submitted = st.form_submit_button("📝 Register & Continue", type="primary", use_container_width=True)
        
        if submitted:
            # Validation
            if not name.strip():
                st.error("Please enter your name")
                return False
            if not grade:
                st.error("Please select your grade level")
                return False
            if not age:
                st.error("Please enter your age")
                return False
            
            # Store registration data
            st.session_state['student_info'] = {
                'name': name.strip(),
                'grade': grade,
                'age': age
            }
            st.session_state['page'] = 'test_generator'
            st.success(f"✅ Welcome {name}! Redirecting to test generation...")
            st.rerun()
            return True
    
    return False

def show_test_generator_page():
    """Show test generation and taking interface"""
    # Header with student info
    student_info = st.session_state['student_info']
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("🎓 Learning Platform - Test Generator")
        st.markdown(f"### Welcome back, **{student_info['name']}**!")
        
    with col2:
        if st.button("👤 Change Student", type="secondary"):
            # Clear session and go back to registration
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    # Show student info in sidebar
    with st.sidebar:
        st.header("👤 Student Information")
        st.write(f"**Name:** {student_info['name']}")
        st.write(f"**Grade:** {student_info['grade']}")
        st.write(f"**Age:** {student_info['age']}")
        
        st.markdown("---")
        st.header("📋 Test Information")
        st.info("This test covers 4 subjects:\n- Phonological Awareness (5 questions)\n- Mathematics (5 questions)\n- Science (5 questions)\n- General Knowledge (5 questions)\n\n**Total: 20 questions**")
        
        if st.button("🔄 Generate New Test", type="primary"):
            with st.spinner("Generating personalized test... This may take a few minutes."):
                test_output = generate_test()
                st.session_state['test_output'] = test_output
                st.session_state['answers'] = {}
                st.session_state['test_submitted'] = False
                if 'evaluation_report' in st.session_state:
                    del st.session_state['evaluation_report']
                st.success("✅ Test generated successfully!")
                st.rerun()
    
    # Main content
    if 'test_output' not in st.session_state:
        # Welcome message and instructions
        st.markdown("---")
        st.markdown("### 🚀 Ready to Start Your Test?")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.info(f"""
            Hi **{student_info['name']}**! 👋
            
            You're in **{student_info['grade']}** and we'll create a test just for you.
            
            Click **"Generate New Test"** in the sidebar to begin!
            """)
        
        # Show sample question
        st.markdown("---")
        st.markdown("### 📝 Sample Question Format")
        st.markdown("**Question:** What is 2 + 3?")
        option = st.radio(
            "Select your answer:",
            ["a) 4", "b) 5", "c) 6", "d) 7"],
            key="sample",
            index=None,
            label_visibility="collapsed"
        )
    else:
        # Show the test
        show_test_interface()

def show_test_interface():
    """Display the actual test interface"""
    student_info = st.session_state['student_info']
    
    # Parse and display test
    sections = parse_test_output(st.session_state['test_output'])
    
    if 'answers' not in st.session_state:
        st.session_state['answers'] = {}
    
    st.markdown("---")
    st.markdown("### 📚 Your Personalized Test")
    st.markdown("**Instructions:** Answer all questions and do your best!")
    
    # Display each section
    for section_idx, (section_name, questions) in enumerate(sections.items()):
        # Display section normally
        st.markdown(f"## 📚 {section_name}")
        st.markdown("---")
        
        for q_idx, q_data in enumerate(questions):
            question_id = f"{section_name}_{q_idx}"
            
            # Display question
            st.markdown(f"**Question {section_idx * 5 + q_idx + 1}:** {q_data['question']}")
            
            # Create radio button for choices (remove [CORRECT] markers for display)
            choice_labels = [c.replace(' [CORRECT]', '') for c in q_data['choices']]
            selected = st.radio(
                f"Select your answer for question {section_idx * 5 + q_idx + 1}:",
                choice_labels,
                key=question_id,
                index=None,
                label_visibility="collapsed"
            )
            
            # Store answer
            if selected:
                st.session_state['answers'][question_id] = selected
            
            st.markdown("")  # Add spacing
        
        st.markdown("---")
    
    # Submit button
    if 'test_submitted' not in st.session_state:
        st.session_state['test_submitted'] = False
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        if st.button("📤 Submit Test", type="primary", use_container_width=True):
            st.session_state['test_submitted'] = True
            st.rerun()
    
    # Show results after submission
    if st.session_state['test_submitted']:
        answered = len(st.session_state['answers'])
        total = sum(len(questions) for questions in sections.values())
        
        st.success(f"✅ Great job, {student_info['name']}! You answered {answered}/{total} questions.")
        
        # Show answers
        with st.expander("📊 Your Test Results"):
            for section_name, questions in sections.items():
                st.markdown(f"**{section_name}**")
                
                section_answered = 0
                for q_idx, q_data in enumerate(questions):
                    question_id = f"{section_name}_{q_idx}"
                    answer = st.session_state['answers'].get(question_id, "Not answered")
                    if answer != "Not answered":
                        section_answered += 1
                    st.write(f"Q{q_idx + 1}: {answer}")
                
                # Show section completion
                st.write(f"*Completed: {section_answered}/{len(questions)} questions*")
                st.markdown("")
        
        # Get evaluation button
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("🎯 Get AI-Powered Evaluation & Feedback", type="secondary", use_container_width=True):
                with st.spinner("Analyzing your test and generating personalized feedback... This may take a moment."):
                    try:
                        evaluation_report = evaluate_test(
                            test_output=st.session_state['test_output'],
                            student_info=st.session_state['student_info'],
                            answers=st.session_state['answers']
                        )
                        st.session_state['evaluation_report'] = evaluation_report
                        st.success("✅ Evaluation complete!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error during evaluation: {str(e)}")
        
        # Display evaluation if available
        if 'evaluation_report' in st.session_state:
            st.markdown("---")
            with st.expander("📈 Your Personalized Evaluation Report", expanded=True):
                st.markdown(st.session_state['evaluation_report'])
            
            # Download evaluation report
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                st.download_button(
                    label="💾 Download Evaluation Report",
                    data=st.session_state['evaluation_report'],
                    file_name=f"evaluation_{student_info['name'].replace(' ', '_')}.txt",
                    mime="text/plain",
                    use_container_width=True
                )


def generate_test_report(student_info, sections):
    """Generate a formatted test report"""
    report = []
    report.append("="*50)
    report.append("LEARNING PLATFORM - TEST REPORT")
    report.append("="*50)
    report.append(f"Student Name: {student_info['name']}")
    report.append(f"Grade: {student_info['grade']}")
    report.append(f"Age: {student_info['age']}")
    report.append(f"Date: {st.session_state.get('test_date', 'Today')}")
    report.append("")
    
    total_answered = len(st.session_state.get('answers', {}))
    total_questions = sum(len(questions) for questions in sections.values())
    
    report.append(f"Overall Performance: {total_answered}/{total_questions} questions answered")
    report.append("="*50)
    report.append("")
    
    # Section-wise results
    for section_name, questions in sections.items():
        report.append(f"{section_name}:")
        
        section_answered = 0
        for q_idx, q_data in enumerate(questions):
            question_id = f"{section_name}_{q_idx}"
            answer = st.session_state['answers'].get(question_id, "Not answered")
            if answer != "Not answered":
                section_answered += 1
            report.append(f"  Q{q_idx + 1}: {answer}")
        
        report.append(f"  Section Score: {section_answered}/{len(questions)}")
        report.append("")
    
    report.append("="*50)
    report.append("Thank you for using Learning Platform!")
    
    return "\n".join(report)

def parse_test_output(test_output):
    """Parse the generated test output into structured questions"""
    sections = {}
    current_section = None
    questions = []
    
    lines = test_output.split('\n')
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        
        # Check for section headers
        if line.startswith('===') and 'SECTION' in line:
            if current_section and questions:
                sections[current_section] = questions
            
            # Extract section name
            match = re.search(r'===\s*(.+?)\s+SECTION', line)
            if match:
                current_section = match.group(1).strip()
                questions = []
        
        # Check for numbered questions
        elif re.match(r'^\d+\.\s+', line):
            question_text = re.sub(r'^\d+\.\s+', '', line).strip()
            choices = []
            
            # Collect choices
            j = i + 1
            while j < len(lines) and len(choices) < 4:
                choice_line = lines[j].strip()
                if re.match(r'^[a-d]\)', choice_line):
                    choices.append(choice_line)
                    j += 1
                elif choice_line == "":
                    j += 1
                elif re.match(r'^\d+\.', choice_line):
                    break
                else:
                    j += 1
            
            if question_text and len(choices) >= 3:
                questions.append({
                    'question': question_text,
                    'choices': choices[:4]
                })
            
            i = j - 1
        
        i += 1
    
    # Add last section
    if current_section and questions:
        sections[current_section] = questions
    
    return sections

def main():
    # Initialize session state
    if 'page' not in st.session_state:
        st.session_state['page'] = 'registration'
    
    # Page routing
    if st.session_state['page'] == 'registration':
        show_registration_page()
    elif st.session_state['page'] == 'test_generator':
        show_test_generator_page()

if __name__ == "__main__":
    main()
