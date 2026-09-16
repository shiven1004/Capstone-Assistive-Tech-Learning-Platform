import os
os.environ["TOKENIZERS_PARALLELISM"] = "false"

from flask import Flask, render_template, jsonify, request, session, send_from_directory
import sys
import os
import warnings
from datetime import datetime
import time


# Suppress warnings
warnings.filterwarnings("ignore")

# Define paths
base_dir = os.path.dirname(__file__)
test_gen_path = os.path.join(base_dir, "Learning Platform - Test Generation")
learning_path = os.path.join(base_dir, "Learning Platform")
emotional_path = os.path.join(base_dir, "Emotional Chatbot")
audio_dir = os.path.join(base_dir, "audio_files")
os.makedirs(audio_dir, exist_ok=True)

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = 'your-secret-key-change-this'

# ==================== LAZY LOADING FUNCTIONS ====================

def load_test_generation_module():
    """Load test generation module"""
    try:
        sys.path.insert(0, test_gen_path)
        from question_generator import generate_subject_questions, create_enhanced_prompts  # type: ignore
        from evaluation_module import TestEvaluator  # type: ignore
        sys.path.pop(0)
        return generate_subject_questions, create_enhanced_prompts, TestEvaluator
    except Exception as e:
        print(f"Failed to load test generation: {e}")
        return None, None, None

def load_academic_chatbot_module():
    """Load academic chatbot"""
    try:
        # Clear module cache
        for mod in ['model_handler', 'logger']:
            if mod in sys.modules:
                del sys.modules[mod]
        
        sys.path.insert(0, learning_path)
        from academic_generation_pipeline import get_chat_response  # type: ignore
        # Load dynamic resource search and TTS
        sys.path.insert(0, os.path.join(learning_path, "backend"))
        from resource_search import fetch_resources_for_subject, GRADES, SUBJECTS  # type: ignore
        sys.path.pop(0)
        from TTS import TTS  # type: ignore
        sys.path.pop(0)
        return get_chat_response, fetch_resources_for_subject, GRADES, SUBJECTS, TTS
    except Exception as e:
        print(f"Failed to load academic chatbot: {e}")
        return None

def load_emotional_support_module():
    """Load emotional support"""
    try:
        # Clear module cache
        for mod in ['model_handler', 'causal_model_handler', 'logger', 'sequence_model_handler']:
            if mod in sys.modules:
                del sys.modules[mod]
        
        original_cwd = os.getcwd()
        os.chdir(emotional_path)
        sys.path.insert(0, emotional_path)
        
        from emotion_detection_pipeline import EmotionDetector  # type: ignore
        from generation_pipeline import generate_educational_response  # type: ignore
        from TTS import TTS as EmoTTS  # type: ignore
        
        model_path = os.path.join(emotional_path, "out", "deberta_v3_base_emotion")
        
        detector = EmotionDetector(
            model_name=model_path,
            label_file_path=os.path.join(model_path, "labels.json") if os.path.exists(os.path.join(model_path, "labels.json")) else None,
            min_conf=0.45,
            prefer_mps=True
        )
        
        sys.path.pop(0)
        os.chdir(original_cwd)
        
        return detector, generate_educational_response, EmoTTS
    except Exception as e:
        try:
            os.chdir(original_cwd)
        except:
            pass
        print(f"Failed to load emotional support: {e}")
        return None, None, None

# ==================== ROUTES ====================

@app.route('/')
def index():
    """Registration page"""
    return render_template('index.html')

@app.route('/test')
def test():
    """Test page"""
    return render_template('test.html')

@app.route('/dashboard')
def dashboard():
    """Dashboard page"""
    return render_template('dashboard.html')

@app.route('/emotional')
def emotional():
    """Emotional support page"""
    return render_template('emotional.html')

# =============== STATIC AUDIO ===============

@app.route('/audio/<path:filename>')
def audio(filename):
    return send_from_directory(audio_dir, filename)

# ==================== API ENDPOINTS ====================

@app.route('/api/generate-test', methods=['POST'])
def generate_test():
    """Generate test questions"""
    try:
        data = request.json
        user_data = data.get('userData', {})
        
        # Load test generation module
        generate_subject_questions, create_enhanced_prompts, TestEvaluator = load_test_generation_module()
        
        if not generate_subject_questions:
            return jsonify({'success': False, 'error': 'Failed to load test generation module'}), 500
        
        # Generate questions
        subjects = ["Phonological Awareness", "Mathematics", "Science", "General Knowledge"]
        all_questions = {}
        
        for subject in subjects:
            try:
                raw_questions = generate_subject_questions(subject, target=5)
                parsed_questions = []
                
                for q_text in raw_questions:
                    lines = q_text.split('\n')
                    if len(lines) >= 4:
                        question = lines[0].strip()
                        cleaned_choices = []
                        correct_index = None

                        for idx, line in enumerate(lines[1:5]):
                            if not line.strip():
                                continue
                            choice_text = line.strip()
                            if '[CORRECT]' in choice_text:
                                correct_index = len(cleaned_choices)
                            cleaned_choices.append(choice_text.replace(' [CORRECT]', '').replace('[CORRECT]', '').strip())

                        if cleaned_choices:
                            if correct_index is None:
                                correct_index = 0
                            parsed_questions.append({
                                'question': question,
                                'choices': cleaned_choices,
                                'correctIndex': correct_index
                            })
                
                if parsed_questions:
                    all_questions[subject] = parsed_questions
            except Exception as e:
                print(f"Error generating {subject} questions: {e}")
                all_questions[subject] = []
        
        # Ensure we have questions
        if not all_questions or all(len(qs) == 0 for qs in all_questions.values()):
            return jsonify({'success': False, 'error': 'Could not generate questions. Please try again.'}), 500
        
        return jsonify({
            'success': True,
            'questions': all_questions
        })
    
    except Exception as e:
        print(f"Error in generate_test: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/evaluate-test', methods=['POST'])
def evaluate_test():
    """Evaluate test responses"""
    try:
        data = request.json
        user_data = data.get('userData', {})
        answers = data.get('answers', {})
        questions = data.get('questions', {})
        
        # Load evaluation module
        _, _, TestEvaluator = load_test_generation_module()
        
        if not TestEvaluator:
            return jsonify({'success': False, 'error': 'Failed to load evaluation module'}), 500
        
        # Create test output string (reinsert [CORRECT] marker using correctIndex)
        test_output_parts = []
        for section, qs in questions.items():
            test_output_parts.append(f"\n=== {section} SECTION ===\n")
            for i, q in enumerate(qs, 1):
                test_output_parts.append(f"{i}. {q['question']}\n")
                choices = q.get('choices', [])
                correct_idx = q.get('correctIndex') if isinstance(q.get('correctIndex'), int) else None
                if correct_idx is None and choices:
                    # Fallback: try to infer from embedded marker
                    for idx, choice in enumerate(choices):
                        if '[CORRECT]' in choice:
                            correct_idx = idx
                            choices[idx] = choice.replace(' [CORRECT]', '').replace('[CORRECT]', '').strip()
                            break
                if correct_idx is None:
                    correct_idx = 0

                for idx, choice in enumerate(choices):
                    marker = ' [CORRECT]' if idx == correct_idx else ''
                    test_output_parts.append(f"{choice}{marker}\n")
                test_output_parts.append("\n")
        
        test_output = "".join(test_output_parts)
        
        # Evaluate
        evaluator = TestEvaluator(
            test_output=test_output,
            student_info=user_data,
            answers=answers
        )
        
        accuracy = evaluator.calculate_accuracy()
        feedback = evaluator.generate_llm_feedback()
        
        return jsonify({
            'success': True,
            'evaluation': {
                'accuracy': accuracy,
                'feedback': feedback
            }
        })
    
    except Exception as e:
        print(f"Error in evaluate_test: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    """Academic chatbot"""
    try:
        data = request.json
        message = data.get('message', '')
        history = data.get('history', [])
        
        # Load chatbot
        loaded = load_academic_chatbot_module()
        if not loaded:
            return jsonify({
                'success': False,
                'response': 'Sorry, the academic chatbot is temporarily unavailable.'
            }), 500
        get_chat_response, _, _, _, TTS = loaded
        
        # Get response
        response = get_chat_response(message, history)
        # Generate audio
        audio_url = None
        try:
            tts = TTS(engine_name="gtts")
            ts = int(time.time() * 1000)
            filename = f"chat_{ts}.mp3"
            path = os.path.join(audio_dir, filename)
            clean_text = ''.join(ch for ch in response if ord(ch) < 128 or ch.isspace()).strip()
            if clean_text:
                tts.save(clean_text, path)
                audio_url = f"/audio/{filename}"
        except Exception as e:
            print(f"TTS failed (chat): {e}")
        
        return jsonify({
            'success': True,
            'response': response,
            'audio': audio_url
        })
    
    except Exception as e:
        print(f"Error in chat: {e}")
        return jsonify({
            'success': False,
            'response': 'Sorry, I encountered an error. Please try again.'
        }), 500

@app.route('/api/emotional-support', methods=['POST'])
def emotional_support():
    """Emotional support chatbot"""
    try:
        data = request.json
        message = data.get('message', '')
        history = data.get('history', [])
        
        # Load emotional support modules
        emotion_detector, generate_educational_response, EmoTTS = load_emotional_support_module()
        
        if not emotion_detector or not generate_educational_response or not EmoTTS:
            return jsonify({
                'success': False,
                'response': 'Emotional support is temporarily unavailable.'
            }), 500
        
        # Detect emotion
        emotion_analysis = emotion_detector.detect_educational_emotion(message)
        
        # Generate response
        response = generate_educational_response(message, emotion_analysis)
        # Generate audio
        audio_url = None
        try:
            tts = EmoTTS(engine_name="gtts")
            ts = int(time.time() * 1000)
            filename = f"emo_{ts}.mp3"
            path = os.path.join(audio_dir, filename)
            clean_text = ''.join(ch for ch in response if ord(ch) < 128 or ch.isspace()).strip()
            if clean_text:
                tts.save(clean_text, path)
                audio_url = f"/audio/{filename}"
        except Exception as e:
            print(f"TTS failed (emotional): {e}")
        
        return jsonify({
            'success': True,
            'response': response,
            'emotion': emotion_analysis,
            'audio': audio_url
        })
    
    except Exception as e:
        print(f"Error in emotional_support: {e}")
        return jsonify({
            'success': False,
            'response': 'I\'m here for you. Could you tell me more about how you\'re feeling?'
        }), 500

# ==================== ERROR HANDLERS ====================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({'error': 'Internal server error'}), 500

# ==================== MAIN ====================

@app.route('/api/resources', methods=['POST'])
def resources():
    try:
        data = request.json or {}
        grade = data.get('grade')
        subject = data.get('subject')
        if not grade or not subject:
            return jsonify({'error': 'Missing grade or subject'}), 400
        loaded = load_academic_chatbot_module()
        if not loaded:
            return jsonify({'error': 'Resource module unavailable'}), 500
        _, fetch_resources_for_subject, _, _, _ = loaded
        result = fetch_resources_for_subject(grade, subject)
        return jsonify(result)
    except Exception as e:
        print(f"Error in resources API: {e}")
        return jsonify({'error': 'Failed to fetch resources'}), 500

# ==================== MAIN ====================

if __name__ == '__main__':
    app.run(
        host='127.0.0.1',
        port=5001,
        debug=False,
        threaded=False,      # ✅ CRITICAL: Disable threading
        processes=1,         # ✅ Single process only
        use_reloader=False   # ✅ Prevent double model loading
    )