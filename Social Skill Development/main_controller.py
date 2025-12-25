import threading
import time
import sys

# ================= IMPORT MODULES =================
from text_to_speech.realtime_tts import speak
from video_to_text.realtime_stt import listen_once
from emotion_detection.real_time_emotion import start_emotion_detection
from assessment.questions import get_random_question
from assessment.llm_evaluator import evaluate_with_llm
from assessment.show_image import show_question_image


# ================= ASSESSMENT PIPELINE =================
def run_assessment():
    """
    Runs:
    Question → (optional image) → TTS → STT → LLM feedback
    """
    try:
        # Let camera & mic warm up
        time.sleep(2)

        q = get_random_question()

        question_text = q["question"]
        image_path = q["image"]

        print("\n📝 Question:", question_text)

        # Show image ONLY if present (in background thread - safe)
        if image_path:
            try:
                image_thread = threading.Thread(
                    target=show_question_image,
                    args=(image_path,),
                    daemon=True
                )
                image_thread.start()
            except Exception as e:
                print(f"⚠️ Image display error: {e}")

        # Speak the question
        speak(question_text)

        # Listen for answer
        student_answer = listen_once()

        if not student_answer or student_answer.strip() == "":
            print("⚠️ No response detected")
            speak("That's okay. We can try again later.")
            return

        print("🗣 Student Answer:", student_answer)

        # LLM evaluation (safe wrapper)
        try:
            feedback = evaluate_with_llm(
                question=question_text,
                skills=q.get("skills", ["communication"]),
                student_answer=student_answer
            )
        except Exception as e:
            print("❌ LLM Error:", e)
            feedback = "Thank you for answering. You did well."

        print("\n📊 Feedback:", feedback)

        speak("Thank you for your answer.")
        speak(feedback)
        
    except Exception as e:
        print(f"❌ Assessment error: {e}")
        import traceback
        traceback.print_exc()


# ================= MAIN CONTROLLER =================
if __name__ == "__main__":
    print("🚀 Starting Multimodal Learning Assessment System")
    
    try:
        # Start assessment in background thread (safe - no camera operations)
        assessment_thread = threading.Thread(
            target=run_assessment,
            daemon=False
        )
        assessment_thread.start()
        
        # Wait for assessment to complete before starting emotion detection
        assessment_thread.join(timeout=120)  # Wait max 2 minutes
        
        # Emotion detection MUST run in main thread on macOS (OpenCV requirement)
        # This is now after assessment, preventing threading conflicts
        print("\n📹 Starting emotion detection monitoring...")
        start_emotion_detection(duration=30)
        
    except KeyboardInterrupt:
        print("\n⏹️  Assessment interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
