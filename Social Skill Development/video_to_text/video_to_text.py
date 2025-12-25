import whisper
import subprocess
import os

#used ffmpeg to convert video to audio

video_file = "video.mov"
audio_file = "audio.wav"

output_text_file = "output.txt"

print("🎬 Converting video to audio...")

subprocess.run([
    "ffmpeg", "-y", "-i", video_file,
    "-ac", "1", "-ar", "16000",
    audio_file
])

print("Audio extracted!")

print("Loading Whisper model...")
model = whisper.load_model("base")

print("Transcribing audio...")
result = model.transcribe(audio_file)

text = result["text"]

# Save output to text file
with open(output_text_file, "w", encoding="utf-8") as f:
    f.write(text)

print("Transcription completed!")
print("Transcribed Text:\n")
print(text)
print("\nSaved to:", output_text_file)
