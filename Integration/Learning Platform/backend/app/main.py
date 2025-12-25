from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import os
import time

from logger import Logger
from academic_generation_pipeline import get_chat_response
from ..resource_search import fetch_resources_for_subject, GRADES, SUBJECTS
from TTS import TTS

app = FastAPI(title="Learning Platform")

# CORS (optional)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Logging
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
log_dir = os.path.join(ROOT_DIR, "Logs")
os.makedirs(log_dir, exist_ok=True)
logger = Logger(name="FastAPI-Frontend", log_file_needed=True, log_file=os.path.join(log_dir, "fastapi_frontend.log"), level="DEV")

# Templates and static files
BASE_DIR = os.path.dirname(__file__)
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")
app.mount("/audio", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "..", "audio_files")), name="audio")

class ChatRequest(BaseModel):
    message: str
    history: list | None = None

class ResourceRequest(BaseModel):
    grade: str
    subject: str

# TTS engine (lazy init)
tts_engine = None

def get_tts():
    global tts_engine
    if tts_engine is None:
        try:
            tts_engine = TTS(engine_name="gtts")
            logger.info("TTS engine initialized (gTTS)")
        except Exception as e:
            logger.error(f"Failed to initialize TTS: {e}")
            tts_engine = None
    return tts_engine

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "grades": GRADES,
        "subjects": SUBJECTS,
    })

@app.post("/api/chat")
async def api_chat(req: ChatRequest):
    msg = (req.message or "").strip()
    if not msg:
        raise HTTPException(status_code=400, detail="Message cannot be empty")
    try:
        logger.info(f"Chat message: {msg[:100]}")
        response = get_chat_response(msg, req.history or [])
        # Generate audio
        audio_url = None
        tts = get_tts()
        if tts:
            try:
                audio_dir = os.path.join(os.path.dirname(__file__), "..", "audio_files")
                os.makedirs(audio_dir, exist_ok=True)
                ts = int(time.time() * 1000)
                filename = f"resp_{ts}.mp3"
                path = os.path.join(audio_dir, filename)
                tts.save(response, path)
                audio_url = f"/audio/{filename}"
                logger.debug(f"Audio created: {path}")
            except Exception as e:
                logger.warning(f"Audio generation failed: {e}")
        return JSONResponse({"text": response, "audio": audio_url})
    except Exception as e:
        logger.error(f"Chat API error: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate response")

@app.post("/api/resources")
async def api_resources(req: ResourceRequest):
    try:
        logger.info(f"Resources request: {req.grade} - {req.subject}")
        data = fetch_resources_for_subject(req.grade, req.subject)
        return JSONResponse(data)
    except Exception as e:
        logger.error(f"Resources API error: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch resources")
