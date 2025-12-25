#!/usr/bin/env python3
"""
Text-to-Speech Converter
- CLI mode
- Tkinter GUI mode
Supports pyttsx3 (offline) and gTTS (online).
Saves to WAV (pyttsx3) or MP3 (gTTS), and can convert WAV->MP3 via pydub if ffmpeg is present.
"""


import sys
import os
import argparse
import threading
import tempfile
import traceback

# GUI imports
try:
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox
except Exception:
    tk = None

# TTS engines
try:
    import pyttsx3
except Exception:
    pyttsx3 = None

try:
    from gtts import gTTS
except Exception:
    gTTS = None

# Playback/conversion
try:
    from playsound import playsound
except Exception:
    playsound = None

try:
    from pydub import AudioSegment
except Exception:
    AudioSegment = None

# Utilities
def safe_print(*a, **k):
    try:
        print(*a, **k)
    except Exception:
        pass

class TTS:
    def __init__(self, engine_name="pyttsx3"):
        self.engine_name = engine_name
        self.p_engine = None
        if engine_name == "pyttsx3" and pyttsx3:
            try:
                self.p_engine = pyttsx3.init()
            except Exception as e:
                safe_print("pyttsx3 init failed:", e)
                self.p_engine = None

    def list_voices(self):
        if self.engine_name == "pyttsx3" and self.p_engine:
            try:
                voices = self.p_engine.getProperty("voices")
                return [(v.id, getattr(v, "name", str(v.id))) for v in voices]
            except Exception:
                return []
        # gTTS does not provide voices via API (it uses Google backend)
        return []

    def speak(self, text, rate=None, volume=None, voice_id=None):
        if not text:
            return
        if self.engine_name == "pyttsx3":
            if not pyttsx3 or not self.p_engine:
                raise RuntimeError("pyttsx3 not available")
            if rate is not None:
                try:
                    self.p_engine.setProperty("rate", int(rate))
                except Exception:
                    pass
            if volume is not None:
                try:
                    v = float(volume)
                    if 0.0 <= v <= 1.0:
                        self.p_engine.setProperty("volume", v)
                except Exception:
                    pass
            if voice_id:
                try:
                    self.p_engine.setProperty("voice", voice_id)
                except Exception:
                    pass
            # speak
            self.p_engine.say(text)
            self.p_engine.runAndWait()
        elif self.engine_name == "gtts":
            if not gTTS:
                raise RuntimeError("gTTS not available")
            # save to temp mp3 then play
            t = gTTS(text=text)
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
            tmp.close()
            try:
                t.save(tmp.name)
                if playsound:
                    playsound(tmp.name)
                else:
                    safe_print("playsound not installed; saved MP3 at", tmp.name)
            finally:
                try:
                    os.unlink(tmp.name)
                except Exception:
                    pass
        else:
            raise RuntimeError("Unknown engine: " + str(self.engine_name))

    def save(self, text, filename, rate=None, volume=None, voice_id=None):
        filename = os.path.abspath(filename)
        ext = os.path.splitext(filename)[1].lower()
        if self.engine_name == "pyttsx3":
            if not pyttsx3 or not self.p_engine:
                raise RuntimeError("pyttsx3 not available")
            # pyttsx3 can save to file via save_to_file (usually wav)
            # If user requests mp3, we will save wav first and convert (if pydub available)
            if ext == ".mp3":
                # save wav temp
                tmpwav = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
                tmpwav.close()
                try:
                    eng = pyttsx3.init()
                    if rate is not None:
                        eng.setProperty("rate", int(rate))
                    if volume is not None:
                        try:
                            eng.setProperty("volume", float(volume))
                        except Exception:
                            pass
                    if voice_id:
                        try:
                            eng.setProperty("voice", voice_id)
                        except Exception:
                            pass
                    eng.save_to_file(text, tmpwav.name)
                    eng.runAndWait()
                    # convert wav -> mp3
                    if AudioSegment:
                        AudioSegment.from_wav(tmpwav.name).export(filename, format="mp3")
                    else:
                        raise RuntimeError("pydub/ffmpeg required to convert WAV to MP3")
                finally:
                    try:
                        os.unlink(tmpwav.name)
                    except Exception:
                        pass
            else:
                # WAV or other extensions - try saving wav if extension not mp3
                eng = pyttsx3.init()
                if rate is not None:
                    eng.setProperty("rate", int(rate))
                if volume is not None:
                    try:
                        eng.setProperty("volume", float(volume))
                    except Exception:
                        pass
                if voice_id:
                    try:
                        eng.setProperty("voice", voice_id)
                    except Exception:
                        pass
                eng.save_to_file(text, filename)
                eng.runAndWait()
        elif self.engine_name == "gtts":
            if not gTTS:
                raise RuntimeError("gTTS not available")
            # gTTS saves MP3 natively
            if ext != ".mp3":
                # if they requested wav, we save mp3 then convert if pydub exists
                tmpmp3 = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
                tmpmp3.close()
                try:
                    t = gTTS(text=text)
                    t.save(tmpmp3.name)
                    if ext == ".wav":
                        if AudioSegment:
                            AudioSegment.from_mp3(tmpmp3.name).export(filename, format="wav")
                        else:
                            raise RuntimeError("pydub/ffmpeg required to convert MP3 to WAV")
                    else:
                        # unknown extension: default to mp3
                        os.replace(tmpmp3.name, filename)
                        tmpmp3 = None
                finally:
                    try:
                        if tmpmp3:
                            os.unlink(tmpmp3.name)
                    except Exception:
                        pass
            else:
                t = gTTS(text=text)
                t.save(filename)
        else:
            raise RuntimeError("Unknown engine: " + str(self.engine_name))

def run_cli(args):
    engine_name = args.engine
    t = TTS(engine_name)
    if engine_name == "pyttsx3":
       args.voice = "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Speech\\Voices\\Tokens\\TTS_MS_EN-US_ZIRA_11.0"

    if args.list_voices and engine_name == "pyttsx3":
        voices = t.list_voices()
        for vid, name in voices:
            print(vid, " -> ", name) 
        return
    text = args.text or ""
    if not text and args.file:
        try:
            with open(args.file, "r", encoding="utf-8") as f:
                text = f.read()
        except Exception as e:
            print("Failed to read file:", e)
            return
    if not text:
        print("No text provided. Use --text or --file")
        return
    if args.save:
        try:
            t.save(text, args.save, rate=args.rate, volume=args.volume, voice_id=args.voice)
            print("Saved to", args.save)
        except Exception as e:
            print("Save failed:", str(e))
            traceback.print_exc()
    else:
        try:
            t.speak(text, rate=args.rate, volume=args.volume, voice_id=args.voice)
        except Exception as e:
            print("Speak failed:", str(e))
            traceback.print_exc()

# -------- GUI --------
class TTSApp:
    def __init__(self, root):
        self.root = root
        root.title("Text → Speech")
        root.geometry("760x520")
        self.engine_var = tk.StringVar(value="pyttsx3" if pyttsx3 else ("gtts" if gTTS else "none"))
        self.rate_var = tk.IntVar(value=150)
        self.volume_var = tk.DoubleVar(value=1.0)
        self.voice_var = tk.StringVar(value="")
        self.status_var = tk.StringVar(value="Ready")
        self.create_widgets()
        self.update_voices()

    def create_widgets(self):
        frm = ttk.Frame(self.root, padding=12)
        frm.pack(fill=tk.BOTH, expand=True)

        top = ttk.Frame(frm)
        top.pack(fill=tk.X, pady=(0,8))

        ttk.Label(top, text="Engine:").pack(side=tk.LEFT)
        eng_combo = ttk.Combobox(top, textvariable=self.engine_var, values=self.detect_engines(), state="readonly", width=12)
        eng_combo.pack(side=tk.LEFT, padx=(6,12))
        eng_combo.bind("<<ComboboxSelected>>", lambda e: self.update_voices())

        ttk.Label(top, text="Rate:").pack(side=tk.LEFT)
        ttk.Scale(top, variable=self.rate_var, from_=80, to=300, orient=tk.HORIZONTAL, length=200).pack(side=tk.LEFT, padx=6)
        ttk.Label(top, text="Volume:").pack(side=tk.LEFT, padx=(12,0))
        ttk.Scale(top, variable=self.volume_var, from_=0.0, to=1.0, orient=tk.HORIZONTAL, length=120).pack(side=tk.LEFT, padx=6)

        ttk.Label(top, text="Voice:").pack(side=tk.LEFT, padx=(12,0))
        self.voice_combo = ttk.Combobox(top, textvariable=self.voice_var, values=[], width=30)
        self.voice_combo.pack(side=tk.LEFT, padx=6)

        txt_frame = ttk.LabelFrame(frm, text="Input text")
        txt_frame.pack(fill=tk.BOTH, expand=True)
        self.text_widget = tk.Text(txt_frame, wrap=tk.WORD)
        self.text_widget.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        btn_frame = ttk.Frame(frm)
        btn_frame.pack(fill=tk.X, pady=6)
        ttk.Button(btn_frame, text="Play", command=self.on_play).pack(side=tk.LEFT, padx=6)
        ttk.Button(btn_frame, text="Save...", command=self.on_save).pack(side=tk.LEFT)
        ttk.Button(btn_frame, text="Load from file...", command=self.on_load_file).pack(side=tk.LEFT, padx=6)
        ttk.Button(btn_frame, text="Clear", command=lambda: self.text_widget.delete("1.0", tk.END)).pack(side=tk.LEFT)

        status = ttk.Label(frm, textvariable=self.status_var, anchor=tk.W, relief=tk.SUNKEN)
        status.pack(fill=tk.X, pady=(8,0))

    def detect_engines(self):
        engines = []
        if pyttsx3:
            engines.append("pyttsx3")
        if gTTS:
            engines.append("gtts")
        if not engines:
            engines = ["none"]
        return engines

    def update_voices(self):
        eng = self.engine_var.get()
        t = TTS(eng)
        voices = t.list_voices()
        if voices:
            display = [f"{name} ({vid})" for vid, name in voices]
            self.voice_combo.config(values=display)
            # set default to first
            self.voice_combo.set(display[0])
        else:
            self.voice_combo.config(values=[])
            self.voice_combo.set("")

    def on_play(self):
        text = self.text_widget.get("1.0", tk.END).strip()
        if not text:
            messagebox.showinfo("Empty", "Please enter some text.")
            return
        self.set_status("Speaking...")
        def work():
            try:
                engine = self.engine_var.get()
                tts = TTS(engine)
                voice_id = None
                if engine == "pyttsx3":
                    v = self.voice_combo.get()
                    if v:
                        # extract id from "name (id)" if possible
                        if "(" in v and v.endswith(")"):
                            voice_id = v.split("(")[-1][:-1]
                        else:
                            voice_id = v
                tts.speak(text, rate=self.rate_var.get(), volume=self.volume_var.get(), voice_id=voice_id)
            except Exception as e:
                safe_print("Play error:", e)
                messagebox.showerror("Error", f"Playback failed:\n{e}")
            finally:
                self.set_status("Ready")
        threading.Thread(target=work, daemon=True).start()

    def on_save(self):
        text = self.text_widget.get("1.0", tk.END).strip()
        if not text:
            messagebox.showinfo("Empty", "Please enter some text.")
            return
        fpath = filedialog.asksaveasfilename(defaultextension=".mp3", filetypes=[("MP3","*.mp3"),("WAV","*.wav"),("All files","*.*")])
        if not fpath:
            return
        self.set_status("Saving...")
        def work():
            try:
                engine = self.engine_var.get()
                tts = TTS(engine)
                voice_id = None
                if engine == "pyttsx3":
                    v = self.voice_combo.get()
                    if v:
                        if "(" in v and v.endswith(")"):
                            voice_id = v.split("(")[-1][:-1]
                        else:
                            voice_id = v
                tts.save(text, fpath, rate=self.rate_var.get(), volume=self.volume_var.get(), voice_id=voice_id)
                messagebox.showinfo("Saved", f"Saved to {fpath}")
            except Exception as e:
                safe_print("Save error:", e)
                messagebox.showerror("Error", f"Save failed:\n{e}")
            finally:
                self.set_status("Ready")
        threading.Thread(target=work, daemon=True).start()

    def on_load_file(self):
        f = filedialog.askopenfilename(filetypes=[("Text files","*.txt"),("All files","*.*")])
        if not f:
            return
        try:
            with open(f, "r", encoding="utf-8") as fh:
                data = fh.read()
            self.text_widget.delete("1.0", tk.END)
            self.text_widget.insert(tk.END, data)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file:\n{e}")

    def set_status(self, s):
        self.status_var.set(s)

def main():
    parser = argparse.ArgumentParser(description="Text-to-Speech converter (CLI & GUI).")
    parser.add_argument("--gui", action="store_true", help="Launch GUI")
    parser.add_argument("--text", type=str, help="Text to speak")
    parser.add_argument("--file", type=str, help="Read text from file")
    parser.add_argument("--engine", type=str, default="pyttsx3", help="Engine: pyttsx3 or gtts")
    parser.add_argument("--rate", type=int, help="Speech rate (pyttsx3)")
    parser.add_argument("--volume", type=float, help="Volume 0.0-1.0")
    parser.add_argument("--voice", type=str, help="Voice id (pyttsx3)")
    parser.add_argument("--save", type=str, help="Save output to file (.mp3 or .wav)")
    parser.add_argument("--list-voices", action="store_true", help="List available voices (pyttsx3)")
    args = parser.parse_args()

    if args.gui:
        if not tk:
            print("tkinter not available on this Python build.")
            return
        root = tk.Tk()
        app = TTSApp(root)
        root.mainloop()
    else:
        run_cli(args)

if __name__ == "__main__":
    main()
