import speech_recognition as sr

recognizer = sr.Recognizer()
microphone = sr.Microphone()

def listen_once():
    with microphone as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        print("🎤 Listening...")
        audio = recognizer.listen(source)

    try:
        text = recognizer.recognize_google(audio)
        print("📝 You said:", text)
        return text

    except sr.UnknownValueError:
        print("❌ Could not understand audio")
        return ""

    except sr.RequestError:
        print("❌ Speech recognition service error")
        return ""
