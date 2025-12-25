import pyttsx3
import threading
import queue

# Thread-safe queue for speech requests
speech_queue = queue.Queue()

# Initialize TTS engine once
engine = pyttsx3.init()
engine.setProperty('rate', 165)      # Speech speed
engine.setProperty('volume', 1.0)    # Max volume

# Optional: set female voice if available
voices = engine.getProperty('voices')
for v in voices:
    if "female" in v.name.lower():
        engine.setProperty('voice', v.id)
        break


def tts_worker():
    """
    Background thread that speaks text sequentially
    """
    while True:
        text = speech_queue.get()
        if text is None:
            break

        engine.say(text)
        engine.runAndWait()
        speech_queue.task_done()


# Start TTS worker thread
tts_thread = threading.Thread(target=tts_worker, daemon=True)
tts_thread.start()


def speak(text: str):
    """
    Public function used by main_controller.py
    """
    if not text or not isinstance(text, str):
        return

    print("🔊 TTS:", text)
    speech_queue.put(text)


def stop_tts():
    """
    Gracefully stop TTS engine
    """
    speech_queue.put(None)
