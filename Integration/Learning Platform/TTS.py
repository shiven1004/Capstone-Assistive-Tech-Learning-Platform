#!/usr/bin/env python3
"""
Text-to-Speech Converter for Educational Chatbot
Supports gTTS (Google Text-to-Speech) for MP3 generation.
"""

import os
import tempfile
import io

try:
    from gtts import gTTS
except Exception:
    gTTS = None

try:
    from pydub import AudioSegment
except Exception:
    AudioSegment = None

class TTS:
    def __init__(self, engine_name="gtts"):
        self.engine_name = engine_name
        if engine_name != "gtts":
            raise RuntimeError("Only gTTS engine is supported")
        if not gTTS:
            raise RuntimeError("gTTS not available")

    def generate_audio_bytes(self, text: str) -> bytes:
        """Generate audio bytes for Streamlit integration"""
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        try:
            tts = gTTS(text=text, lang='en', slow=False)
            audio_bytes = io.BytesIO()
            tts.write_to_fp(audio_bytes)
            audio_bytes.seek(0)
            return audio_bytes.getvalue()
        except Exception as e:
            raise RuntimeError(f"gTTS generation failed: {str(e)}")

    def save(self, text, filename):
        """Save text as MP3 file"""
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        filename = os.path.abspath(filename)
        ext = os.path.splitext(filename)[1].lower()
        
        if ext == ".mp3":
            tts = gTTS(text=text, lang='en', slow=False)
            tts.save(filename)
        elif ext == ".wav":
            if not AudioSegment:
                raise RuntimeError("pydub required to convert MP3 to WAV")
            
            tmpmp3 = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
            tmpmp3.close()
            try:
                tts = gTTS(text=text, lang='en', slow=False)
                tts.save(tmpmp3.name)
                AudioSegment.from_mp3(tmpmp3.name).export(filename, format="wav")
            finally:
                try:
                    os.unlink(tmpmp3.name)
                except Exception:
                    pass
        else:
            tts = gTTS(text=text, lang='en', slow=False)
            tts.save(filename)


