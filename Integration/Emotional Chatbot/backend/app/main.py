from __future__ import annotations
import os
import sys
import time
from pathlib import Path
from typing import Optional, Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

# Ensure repo root is importable
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from logger import Logger  # type: ignore
from emotion_detection_pipeline import detect_enhanced_emotion  # type: ignore
from generation_pipeline import generate_educational_response  # type: ignore
from TTS import TTS  # type: ignore
try:
    # Reuse Learning Platform resource search (dynamic DuckDuckGo-based)
    from pathlib import Path as _Path
    _LP_BACKEND = REPO_ROOT / "Learning Platform" / "backend"
    if str(_LP_BACKEND) not in sys.path:
        sys.path.insert(0, str(_LP_BACKEND))
    from resource_search import fetch_resources_for_subject as lp_fetch_resources, GRADES as LP_GRADES, SUBJECTS as LP_SUBJECTS  # type: ignore
except Exception as _e:
    lp_fetch_resources = None
    LP_GRADES = ["Grade 1", "Grade 2", "Grade 3", "Grade 4", "Grade 5"]
    LP_SUBJECTS = ["English", "Maths", "Science"]

logger = Logger(name="Educational Chatbot API", log_file_needed=True, log_file="Logs/api.log", level="DEV")

app = FastAPI(title="Educational Chatbot API", version="1.0.0")

# If you plan to open the HTML directly from this server, CORS isn't strictly needed,
# but keep it relaxed for local dev.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Paths
WEB_DIR = REPO_ROOT / "web"
WEB_DIR.mkdir(exist_ok=True)
AUDIO_DIR = REPO_ROOT / "audio_files"
AUDIO_DIR.mkdir(exist_ok=True)

# Serve static assets (CSS/JS)
app.mount("/static", StaticFiles(directory=str(WEB_DIR)), name="static")
# Serve generated audio files
app.mount("/audio", StaticFiles(directory=str(AUDIO_DIR)), name="audio")

# Singleton TTS
_tts: Optional[TTS] = None

@app.on_event("startup")
def startup_event():
    global _tts
    try:
        _tts = TTS(engine_name="gtts")
        logger.info("TTS engine initialized (gTTS)")
    except Exception as e:
        logger.error(f"Failed to initialize TTS: {e}")
        _tts = None

# Root route returns the HTML frontend
@app.get("/")
def root():
    index = WEB_DIR / "index.html"
    if not index.exists():
        raise HTTPException(status_code=404, detail="Frontend not found (index.html)")
    return FileResponse(str(index))

class ChatRequest(BaseModel):
    text: str
    context: Optional[Dict[str, Any]] = None

class ChatResponse(BaseModel):
    emotion_analysis: Dict[str, Any]
    reply: str
    audio_url: Optional[str] = None

class TTSRequest(BaseModel):
    text: str
    response_id: Optional[int] = None

class TTSResponse(BaseModel):
    audio_url: str

class ResourceRequest(BaseModel):
    grade: str
    subject: str

class ResourceResponse(BaseModel):
    subject: str
    topic: str
    grade: str
    links: list

@app.get("/health")
def health() -> Dict[str, str]:
    return {"status": "ok"}

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest) -> ChatResponse:
    text = (req.text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="Text cannot be empty")

    logger.debug(f"User: {text}")

    # Emotion analysis
    try:
        emotion = detect_enhanced_emotion(text, req.context or {})
    except Exception as e:
        logger.error(f"Emotion detection failed: {e}")
        raise HTTPException(status_code=500, detail="Emotion detection failed")

    # Response generation
    try:
        reply = generate_educational_response(text, emotion)
    except Exception as e:
        logger.error(f"Response generation failed: {e}")
        raise HTTPException(status_code=500, detail="Response generation failed")

    audio_url: Optional[str] = None
    # TTS audio generation (optional)
    try:
        if _tts is not None:
            ts = int(time.time())
            filename = AUDIO_DIR / f"response_{ts}.mp3"
            # clean text to ASCII for robustness
            clean_text = ''.join(ch for ch in reply if ord(ch) < 128 or ch.isspace()).strip()
            if clean_text:
                _tts.save(clean_text, str(filename))
                if filename.exists() and filename.stat().st_size > 0:
                    audio_url = f"/audio/{filename.name}"
                    logger.debug(f"Audio file generated: {filename} size={filename.stat().st_size} bytes")
    except Exception as e:
        logger.warning(f"TTS generation failed (continuing without audio): {e}")

    return ChatResponse(emotion_analysis=emotion, reply=reply, audio_url=audio_url)

@app.post("/tts", response_model=TTSResponse)
def tts(req: TTSRequest) -> TTSResponse:
    text = (req.text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="Text cannot be empty")
    if _tts is None:
        raise HTTPException(status_code=503, detail="TTS engine unavailable")

    ts = int(time.time()) if req.response_id is None else req.response_id
    filename = AUDIO_DIR / f"response_{ts}.mp3"

    try:
        clean_text = ''.join(ch for ch in text if ord(ch) < 128 or ch.isspace()).strip()
        if not clean_text:
            raise ValueError("No valid text after cleaning")
        _tts.save(clean_text, str(filename))
        if filename.exists() and filename.stat().st_size > 0:
            return TTSResponse(audio_url=f"/audio/{filename.name}")
        raise RuntimeError("Audio file not created")
    except Exception as e:
        logger.error(f"TTS save failed: {e}")
        raise HTTPException(status_code=500, detail="TTS generation failed")

@app.post("/resources", response_model=ResourceResponse)
def resources(req: ResourceRequest):
    if lp_fetch_resources is None:
        raise HTTPException(status_code=503, detail="Resource search unavailable")
    try:
        data = lp_fetch_resources(req.grade, req.subject)
        return JSONResponse(data)
    except Exception as e:
        logger.error(f"Resource fetch failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch resources")

# Entrypoint (run from repo root):
# uvicorn backend.app.main:app --reload --port 8000
