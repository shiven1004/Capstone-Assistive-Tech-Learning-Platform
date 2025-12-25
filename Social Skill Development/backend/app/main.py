from fastapi import FastAPI
from fastapi.responses import HTMLResponse, FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import sys
import threading
import cv2
import numpy as np
import time

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from assessment.questions import get_random_question
from assessment.llm_evaluator import evaluate_with_llm
from text_to_speech.realtime_tts import speak
from emotion_detection.real_time_emotion import EngagementEstimator

# Global emotion state and camera
emotion_state = {
    "emotion": "Neutral",
    "confidence": 0.0,
    "engagement_level": None,
    "engagement_score": None,
}
camera = None
emotion_thread = None
running = False

def start_emotion_detection():
    """Start emotion detection in background thread with real camera"""
    global camera, running
    try:
        running = True
        
        def detect_loop():
            global emotion_state, camera
            
            print("📹 Initializing camera for emotion detection...")
            local_camera = None
            estimator = None
            
            try:
                local_camera = cv2.VideoCapture(0)
                
                if not local_camera or not local_camera.isOpened():
                    print("❌ Camera failed to open")
                    return
                
                # Configure camera
                local_camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                local_camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                local_camera.set(cv2.CAP_PROP_FPS, 30)
                
                print("✅ Camera opened successfully for emotion detection")
                
                emotions = ["Happy", "Neutral", "Focused", "Calm", "Engaged"]
                frame_count = 0
                # Initialize engagement estimator (gracefully handles availability)
                try:
                    estimator = EngagementEstimator()
                except Exception as _:
                    estimator = None
                
                while running:
                    try:
                        ret, frame = local_camera.read()
                        
                        if ret and frame is not None:
                            # Process frame - rotate emotions based on frame count
                            # In production, use actual ML model here
                            emotion_idx = (frame_count // 30) % len(emotions)  # Change emotion every ~1 sec
                            engagement = None
                            if estimator is not None:
                                engagement = estimator.analyze_frame(frame)
                            
                            emotion_state = {
                                "emotion": emotions[emotion_idx],
                                "confidence": 0.70 + (frame_count % 30) / 100,
                                "engagement_level": (engagement or {}).get("engagement_level"),
                                "engagement_score": (engagement or {}).get("engagement_score"),
                            }
                            frame_count += 1
                        else:
                            print("⚠️  Failed to read frame from camera")
                            time.sleep(0.1)
                            
                    except Exception as e:
                        print(f"⚠️  Frame processing error: {e}")
                        time.sleep(0.1)
                    
                    time.sleep(0.033)  # ~30 FPS
                        
            except Exception as e:
                print(f"❌ Emotion detection error: {e}")
            finally:
                if local_camera:
                    try:
                        local_camera.release()
                        print("✅ Camera released")
                    except:
                        pass
                if estimator:
                    try:
                        estimator.close()
                    except Exception:
                        pass
        
        thread = threading.Thread(target=detect_loop, daemon=True)
        thread.start()
        print("✅ Emotion detection thread started")
        
    except Exception as e:
        print(f"❌ Failed to start emotion detection: {e}")
        emotion_state = {"emotion": "Unavailable", "confidence": 0.0}

def generate_frames():
    """Generate video frames for streaming with fallback to synthetic video"""
    global camera
    
    local_camera = None
    use_synthetic = False
    
    try:
        # Try to open real camera
        print("📹 Attempting to access real camera...")
        local_camera = cv2.VideoCapture(0)
        
        if not local_camera or not local_camera.isOpened():
            print("⚠️  Real camera not available, using synthetic video demo instead")
            print("   (Grant camera permissions in System Preferences > Security & Privacy > Camera to use real camera)")
            use_synthetic = True
        else:
            # Configure camera
            local_camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            local_camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            local_camera.set(cv2.CAP_PROP_FPS, 30)
            print("✅ Real camera opened successfully!")
    
    except Exception as e:
        print(f"⚠️  Camera error: {e}, using synthetic demo video")
        use_synthetic = True
    
    # Generate frames
    frame_count = 0
    
    while True:
        try:
            frame = None
            
            if use_synthetic:
                # Generate synthetic video frame for demo
                frame = np.ones((480, 640, 3), dtype=np.uint8) * 40  # Dark gray background
                
                # Add gradient
                for y in range(480):
                    intensity = int(40 + (y / 480.0) * 100)
                    frame[y, :] = [intensity, intensity + 20, intensity + 40]
                
                # Draw a circle that moves
                circle_x = int(320 + 200 * np.sin(frame_count * 0.05))
                circle_y = int(240 + 150 * np.cos(frame_count * 0.03))
                cv2.circle(frame, (circle_x, circle_y), 50, (0, 255, 255), -1)
                
                # Add text
                cv2.putText(frame, "Demo Mode - Camera Unavailable", (50, 50), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                cv2.putText(frame, "Grant camera access for live feed", (80, 100), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 1)
                
            else:
                # Use real camera
                success, frame = local_camera.read()
                if not success or frame is None:
                    print(f"⚠️  Failed to read frame {frame_count}, switching to synthetic")
                    use_synthetic = True
                    continue
            
            # Add emotion overlay to both synthetic and real
            if frame is not None:
                emotion_text = f"{emotion_state.get('emotion', 'N/A')} ({emotion_state.get('confidence', 0)*100:.0f}%)"
                cv2.putText(frame, emotion_text, (10, 430), cv2.FONT_HERSHEY_SIMPLEX, 
                           0.7, (0, 255, 0), 2)
                # Engagement overlay (if available)
                level = emotion_state.get('engagement_level')
                score = emotion_state.get('engagement_score')
                if level is not None and score is not None:
                    eng_text = f"Engagement: {level} ({score*100:.0f}%)"
                else:
                    eng_text = "Engagement: N/A"
                cv2.putText(frame, eng_text, (10, 460), cv2.FONT_HERSHEY_SIMPLEX,
                            0.6, (0, 200, 255), 2)
                
                # Encode frame to JPEG
                ret, buffer = cv2.imencode('.jpg', frame)
                if ret:
                    frame_bytes = buffer.tobytes()
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
                    frame_count += 1
                else:
                    print(f"⚠️  Failed to encode frame {frame_count}")
            
            time.sleep(0.033)  # ~30 FPS
            
        except Exception as e:
            print(f"❌ Frame generation error: {e}")
            time.sleep(0.1)
            
    if local_camera:
        try:
            local_camera.release()
        except:
            pass

# Start emotion detection on startup
start_emotion_detection()

app = FastAPI()

# Mount static files
BASE_DIR = Path(__file__).parent
ROOT_DIR = Path(__file__).parent.parent.parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def index():
    with open(BASE_DIR / "templates" / "index.html") as f:
        return f.read()

@app.get("/stream", response_class=HTMLResponse)
async def stream_viewer():
    """Serve the MJPEG stream viewer"""
    with open(BASE_DIR / "templates" / "stream.html") as f:
        return f.read()

@app.get("/api/question")
async def get_question():
    try:
        q = get_random_question()
        return {
            "success": True,
            "question": q["question"],
            "skills": q.get("skills", ["communication"]),
            "image": f"/api/image/{q.get('image')}" if q.get("image") else None
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/image/{file_path:path}")
async def get_image(file_path: str):
    """Serve images from assessment/images directory"""
    try:
        image_path = ROOT_DIR / file_path
        if image_path.exists() and image_path.is_file():
            return FileResponse(image_path)
        else:
            return {"error": "Image not found"}
    except Exception as e:
        return {"error": str(e)}

@app.post("/api/evaluate")
async def evaluate(data: dict):
    try:
        feedback = evaluate_with_llm(
            question=data.get("question", ""),
            skills=data.get("skills", []),
            student_answer=data.get("answer", "")
        )
        return {"success": True, "feedback": feedback}
    except Exception as e:
        return {"success": False, "feedback": "Thank you for your answer.", "error": str(e)}

@app.post("/api/speak")
async def text_to_speech(data: dict):
    try:
        text = data.get("text", "")
        if text:
            speak(text)
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/emotion")
async def get_emotion():
    """Get current emotion detection"""
    return {
        "success": True,
        "emotion": emotion_state.get("emotion", "Neutral"),
        "confidence": emotion_state.get("confidence", 0.0),
        "engagement_level": emotion_state.get("engagement_level"),
        "engagement_score": emotion_state.get("engagement_score"),
    }

@app.get("/api/video_feed")
async def video_feed():
    """Stream video feed from webcam"""
    return StreamingResponse(generate_frames(), 
                           media_type="multipart/x-mixed-replace; boundary=frame")
