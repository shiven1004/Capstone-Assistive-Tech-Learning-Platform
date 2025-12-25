# Capstone Project: Learning Platform, Emotional Support Chatbot, and Social Skill Development

## Introduction
This project is a multi-component educational suite focused on:
- Emotional support chat for learners.
- A learning resource finder with text-to-speech.
- Test generation and evaluation tools.
- Social skill development utilities including real-time TTS/STT and emotion detection.

It is organized into two primary workspaces:
- [Integration](Integration) — consolidated apps: Emotional Chatbot, Learning Platform, Test Generation, shared logging, datasets, and a vector store.
- [Social Skill Development](Social Skill Development) — real-time TTS/STT, emotion detection, and a small web backend.

## High-level Architecture and Approach
- Emotional Support Chatbot (Integration)
  - Emotion analysis via [`emotion_detection_pipeline`](Integration/Emotional%20Chatbot/emotion_detection_pipeline.py).
  - Educational response generation via [`generation_pipeline`](Integration/Emotional%20Chatbot/generation_pipeline.py), including emoji enhancement like [`EmojiEnhancer._add_special_needs_emojis`](Integration/Emotional%20Chatbot/generation_pipeline.py).
  - Audio via [`TTS`](Integration/Emotional%20Chatbot/TTS.py).
  - Persistent semantic conversation search with FAISS via [`ConversationVectorStore`](Integration/conversation_vectorstore.py) and helper [`log_conversation_to_store`](Integration/conversation_vectorstore.py).
  - CLI and Streamlit UIs: [`main.py`](Integration/Emotional%20Chatbot/main.py), [`streamlit_app.py`](Integration/Emotional%20Chatbot/streamlit_app.py).

- Learning Platform (Integration)
  - Streamlit UI: [`streamlit_app.py`](Integration/Learning%20Platform/streamlit_app.py) with resource search, quick keyword scoring (`ddg_search`, `rerank_kid_friendly`), and audio generation via [`TTS`](Integration/Learning%20Platform/TTS.py).
  - Robust audio generation and cleanup, e.g., [`generate_audio_for_streamlit`](Integration/Learning%20Platform/streamlit_app.py).

- Test Generation (Integration)
  - Streamlit UI and backend for question generation and evaluation: [`streamlit_app.py`](Integration/Learning%20Platform%20-%20Test%20Generation/streamlit_app.py), [`question_generator.py`](Integration/Learning%20Platform%20-%20Test%20Generation/question_generator.py), [`evaluation_module.py`](Integration/Learning%20Platform%20-%20Test%20Generation/evaluation_module.py).
  - LoRA adapters and checkpoints for LLaMA 3.2 under [`llama3.2-past-lora`](Integration/Learning%20Platform%20-%20Test%20Generation/llama3.2-past-lora).

- Social Skill Development
  - Orchestrator: [`main_controller.py`](Social%20Skill%20Development/main_controller.py).
  - Real-time TTS engine using pyttsx3: [`text_to_speech/realtime_tts.py`](Social%20Skill%20Development/text_to_speech/realtime_tts.py) with simple queue and daemon worker.
  - Whisper-based video-to-text and simple real-time STT: [`video_to_text/video_to_text.py`](Social%20Skill%20Development/video_to_text/video_to_text.py), [`video_to_text/realtime_stt.py`](Social%20Skill%20Development/video_to_text/realtime_stt.py).
  - Real-time emotion detection: [`emotion_detection/real_time_emotion.py`](Social%20Skill%20Development/emotion_detection/real_time_emotion.py).
  - Small Flask backend with templates: [`backend/app/main.py`](Social%20Skill%20Development/backend/app/main.py), [`templates`](Social%20Skill%20Development/backend/app/templates).

- Shared Datasets (Integration)
  - Multiple emotional conversation datasets under [`Emotional Chatbot Dataset`](Integration/Emotional%20Chatbot/Emotional%20Chatbot%20Dataset), including SQuAD metrics and tokenizers. Notable utilities: Unicode normalization like `replace_unicode_punct` in XLM tokenizers (e.g., [tokenization_xlm.py](Integration/Emotional%20Chatbot/Emotional%20Chatbot%20Dataset/Emotional-Support-Conversation/Emotional-Support-Conversation-main/codes/src/transformers/models/xlm/tokenization_xlm.py)) and SQuAD metrics like [`compute_predictions_logits`](Integration/Emotional%20Chatbot/Emotional%20Chatbot%20Dataset/Emotional-Support-Conversation/Emotional-Support-Conversation-main/codes/src/transformers/data/metrics/squad_metrics.py).

## Folder Map (key files)
- Integration
  - Entry apps: [`app.py`](Integration/app.py), static and templates: [`static`](Integration/static), [`templates`](Integration/templates).
  - Emotional Chatbot: [`main.py`](Integration/Emotional%20Chatbot/main.py), [`streamlit_app.py`](Integration/Emotional%20Chatbot/streamlit_app.py), [`generation_pipeline.py`](Integration/Emotional%20Chatbot/generation_pipeline.py), [`emotion_detection_pipeline.py`](Integration/Emotional%20Chatbot/emotion_detection_pipeline.py), [`TTS.py`](Integration/Emotional%20Chatbot/TTS.py), [`logger.py`](Integration/Emotional%20Chatbot/logger.py), datasets under [`Emotional Chatbot Dataset`](Integration/Emotional%20Chatbot/Emotional%20Chatbot%20Dataset).
  - Learning Platform: [`streamlit_app.py`](Integration/Learning%20Platform/streamlit_app.py), [`TTS.py`](Integration/Learning%20Platform/TTS.py), [`model_handler.py`](Integration/Learning%20Platform/model_handler.py), resource search backend: [`backend/app`](Integration/Learning%20Platform/backend/app).
  - Test Generation: [`streamlit_app.py`](Integration/Learning%20Platform%20-%20Test%20Generation/streamlit_app.py), [`question_generator.py`](Integration/Learning%20Platform%20-%20Test%20Generation/question_generator.py), [`evaluation_module.py`](Integration/Learning%20Platform%20-%20Test%20Generation/evaluation_module.py), LoRA assets: [`llama3.2-past-lora`](Integration/Learning%20Platform%20-%20Test%20Generation/llama3.2-past-lora).
  - Vector store: [`conversation_vectorstore.py`](Integration/conversation_vectorstore.py).

- Social Skill Development
  - Orchestration: [`main_controller.py`](Social%20Skill%20Development/main_controller.py).
  - Web backend: [`backend/app/main.py`](Social%20Skill%20Development/backend/app/main.py), templates & static.
  - Emotion: [`emotion_detection/real_time_emotion.py`](Social%20Skill%20Development/emotion_detection/real_time_emotion.py).
  - TTS: [`text_to_speech/realtime_tts.py`](Social%20Skill%20Development/text_to_speech/realtime_tts.py), [`text_to_speech/main.py`](Social%20Skill%20Development/text_to_speech/main.py).
  - STT and transcription: [`video_to_text/video_to_text.py`](Social%20Skill%20Development/video_to_text/video_to_text.py), [`video_to_text/realtime_stt.py`](Social%20Skill%20Development/video_to_text/realtime_stt.py).

## Setup

Prerequisites:
- Python 3.10+ recommended.
- ffmpeg (needed for Whisper transcription). macOS: `brew install ffmpeg`, Ubuntu: `sudo apt-get install ffmpeg`.

Create a virtual environment:
- macOS/Linux:
  ```sh
  python3 -m venv .venv
  source .venv/bin/activate
  ```
- Windows (PowerShell):
  ```sh
  py -m venv .venv
  .\.venv\Scripts\Activate.ps1
  ```

Install main dependencies:
```sh
pip install -r Integration/requirements.txt
```

Component-specific extras:
```sh
# Emotional Chatbot (if running standalone)
pip install -r Integration/Emotional\ Chatbot/backend/app/requirements.txt  # if present

# Learning Platform backend extras
pip install -r Integration/Learning\ Platform/backend/requirements.txt      # if present

# Social Skill Development (root requirements)
pip install -r Social\ Skill\ Development/requirements.txt

# Social TTS/STT specific
pip install -r Social\ Skill\ Development/text_to_speech/requirements.txt
pip install -r Social\ Skill\ Development/video_to_text/requirements.txt
```

## How to Run

Run components in separate VS Code terminals as needed.

- Emotional Support Chatbot (CLI):
  ```sh
  cd Integration/Emotional\ Chatbot
  python main.py
  ```
  Uses logging via [`logger.py`](Integration/Emotional%20Chatbot/logger.py) and stores conversations with [`log_conversation_to_store`](Integration/conversation_vectorstore.py).

- Emotional Support Chatbot (Streamlit UI):
  ```sh
  cd Integration/Emotional\ Chatbot
  streamlit run streamlit_app.py
  ```

- Learning Platform (Streamlit UI, resource search + TTS):
  ```sh
  cd Integration/Learning\ Platform
  streamlit run streamlit_app.py
  ```
  Audio generation is handled by [`generate_audio_for_streamlit`](Integration/Learning%20Platform/streamlit_app.py) using [`TTS`](Integration/Learning%20Platform/TTS.py).

- Test Generation Platform (Streamlit UI):
  ```sh
  cd Integration/Learning\ Platform\ -\ Test\ Generation
  streamlit run streamlit_app.py
  ```
  Ensure LoRA assets exist in [`llama3.2-past-lora`](Integration/Learning%20Platform%20-%20Test%20Generation/llama3.2-past-lora).

- Integration Web App (if used):
  ```sh
  cd Integration
  python app.py
  ```

- Social Skill Development — Web Backend:
  ```sh
  cd Social\ Skill\ Development/backend/app
  python main.py
  # Open http://127.0.0.1:5000
  ```

- Social Skill Development — Orchestrator:
  ```sh
  cd Social\ Skill\ Development
  python main_controller.py
  ```

- Social Skill Development — Real-time TTS:
  ```sh
  cd Social\ Skill\ Development/text_to_speech
  python main.py
  # or use the queue-backed engine: python realtime_tts.py
  ```

- Social Skill Development — Whisper Video-to-Text:
  ```sh
  cd Social\ Skill\ Development/video_to_text
  python video_to_text.py
  # requires ffmpeg and will output to output.txt
  ```

- Social Skill Development — Real-time STT (microphone):
  ```sh
  cd Social\ Skill\ Development/video_to_text
  python realtime_stt.py
  ```

## Notes and Troubleshooting
- If audio files are not created, check TTS engines in [`Integration/Learning Platform/TTS.py`](Integration/Learning%20Platform/TTS.py) and [`Integration/Emotional Chatbot/TTS.py`](Integration/Emotional%20Chatbot/TTS.py).
- Whisper requires ffmpeg and may benefit from a GPU.
- FAISS index is saved by [`ConversationVectorStore.save_index`](Integration/conversation_vectorstore.py); ensure `conversation_index/` is writable.
- Datasets are large; make sure paths under [`Emotional Chatbot Dataset`](Integration/Emotional%20Chatbot/Emotional%20Chatbot%20Dataset) remain intact.
- Streamlit apps will choose default ports; use `streamlit run streamlit_app.py --server.port 8502` to choose a custom port when running multiple apps.

## Logs
Logs are written to various `Logs/` folders, e.g., [`Integration/Logs`](Integration/Logs), and via components like [`logger.py`](Integration/Emotional%20Chatbot/logger.py).

## Security and Licensing
- Hugging Face model scripts included under their licenses in the dataset folder.
- Ensure no sensitive data is committed to logs or the FAISS index.

---
```// filepath: /Users/shivenk/Documents/Capstone/README.md
# Capstone Project: Learning Platform, Emotional Support Chatbot, and Social Skill Development

## Introduction
This project is a multi-component educational suite focused on:
- Emotional support chat for learners.
- A learning resource finder with text-to-speech.
- Test generation and evaluation tools.
- Social skill development utilities including real-time TTS/STT and emotion detection.

It is organized into two primary workspaces:
- [Integration](Integration) — consolidated apps: Emotional Chatbot, Learning Platform, Test Generation, shared logging, datasets, and a vector store.
- [Social Skill Development](Social Skill Development) — real-time TTS/STT, emotion detection, and a small web backend.

## High-level Architecture and Approach
- Emotional Support Chatbot (Integration)
  - Emotion analysis via [`emotion_detection_pipeline`](Integration/Emotional%20Chatbot/emotion_detection_pipeline.py).
  - Educational response generation via [`generation_pipeline`](Integration/Emotional%20Chatbot/generation_pipeline.py), including emoji enhancement like [`EmojiEnhancer._add_special_needs_emojis`](Integration/Emotional%20Chatbot/generation_pipeline.py).
  - Audio via [`TTS`](Integration/Emotional%20Chatbot/TTS.py).
  - Persistent semantic conversation search with FAISS via [`ConversationVectorStore`](Integration/conversation_vectorstore.py) and helper [`log_conversation_to_store`](Integration/conversation_vectorstore.py).
  - CLI and Streamlit UIs: [`main.py`](Integration/Emotional%20Chatbot/main.py), [`streamlit_app.py`](Integration/Emotional%20Chatbot/streamlit_app.py).

- Learning Platform (Integration)
  - Streamlit UI: [`streamlit_app.py`](Integration/Learning%20Platform/streamlit_app.py) with resource search, quick keyword scoring (`ddg_search`, `rerank_kid_friendly`), and audio generation via [`TTS`](Integration/Learning%20Platform/TTS.py).
  - Robust audio generation and cleanup, e.g., [`generate_audio_for_streamlit`](Integration/Learning%20Platform/streamlit_app.py).

- Test Generation (Integration)
  - Streamlit UI and backend for question generation and evaluation: [`streamlit_app.py`](Integration/Learning%20Platform%20-%20Test%20Generation/streamlit_app.py), [`question_generator.py`](Integration/Learning%20Platform%20-%20Test%20Generation/question_generator.py), [`evaluation_module.py`](Integration/Learning%20Platform%20-%20Test%20Generation/evaluation_module.py).
  - LoRA adapters and checkpoints for LLaMA 3.2 under [`llama3.2-past-lora`](Integration/Learning%20Platform%20-%20Test%20Generation/llama3.2-past-lora).

- Social Skill Development
  - Orchestrator: [`main_controller.py`](Social%20Skill%20Development/main_controller.py).
  - Real-time TTS engine using pyttsx3: [`text_to_speech/realtime_tts.py`](Social%20Skill%20Development/text_to_speech/realtime_tts.py) with simple queue and daemon worker.
  - Whisper-based video-to-text and simple real-time STT: [`video_to_text/video_to_text.py`](Social%20Skill%20Development/video_to_text/video_to_text.py), [`video_to_text/realtime_stt.py`](Social%20Skill%20Development/video_to_text/realtime_stt.py).
  - Real-time emotion detection: [`emotion_detection/real_time_emotion.py`](Social%20Skill%20Development/emotion_detection/real_time_emotion.py).
  - Small Flask backend with templates: [`backend/app/main.py`](Social%20Skill%20Development/backend/app/main.py), [`templates`](Social%20Skill%20Development/backend/app/templates).

- Shared Datasets (Integration)
  - Multiple emotional conversation datasets under [`Emotional Chatbot Dataset`](Integration/Emotional%20Chatbot/Emotional%20Chatbot%20Dataset), including SQuAD metrics and tokenizers. Notable utilities: Unicode normalization like `replace_unicode_punct` in XLM tokenizers (e.g., [tokenization_xlm.py](Integration/Emotional%20Chatbot/Emotional%20Chatbot%20Dataset/Emotional-Support-Conversation/Emotional-Support-Conversation-main/codes/src/transformers/models/xlm/tokenization_xlm.py)) and SQuAD metrics like [`compute_predictions_logits`](Integration/Emotional%20Chatbot/Emotional%20Chatbot%20Dataset/Emotional-Support-Conversation/Emotional-Support-Conversation-main/codes/src/transformers/data/metrics/squad_metrics.py).

## Folder Map (key files)
- Integration
  - Entry apps: [`app.py`](Integration/app.py), static and templates: [`static`](Integration/static), [`templates`](Integration/templates).
  - Emotional Chatbot: [`main.py`](Integration/Emotional%20Chatbot/main.py), [`streamlit_app.py`](Integration/Emotional%20Chatbot/streamlit_app.py), [`generation_pipeline.py`](Integration/Emotional%20Chatbot/generation_pipeline.py), [`emotion_detection_pipeline.py`](Integration/Emotional%20Chatbot/emotion_detection_pipeline.py), [`TTS.py`](Integration/Emotional%20Chatbot/TTS.py), [`logger.py`](Integration/Emotional%20Chatbot/logger.py), datasets under [`Emotional Chatbot Dataset`](Integration/Emotional%20Chatbot/Emotional%20Chatbot%20Dataset).
  - Learning Platform: [`streamlit_app.py`](Integration/Learning%20Platform/streamlit_app.py), [`TTS.py`](Integration/Learning%20Platform/TTS.py), [`model_handler.py`](Integration/Learning%20Platform/model_handler.py), resource search backend: [`backend/app`](Integration/Learning%20Platform/backend/app).
  - Test Generation: [`streamlit_app.py`](Integration/Learning%20Platform%20-%20Test%20Generation/streamlit_app.py), [`question_generator.py`](Integration/Learning%20Platform%20-%20Test%20Generation/question_generator.py), [`evaluation_module.py`](Integration/Learning%20Platform%20-%20Test%20Generation/evaluation_module.py), LoRA assets: [`llama3.2-past-lora`](Integration/Learning%20Platform%20-%20Test%20Generation/llama3.2-past-lora).
  - Vector store: [`conversation_vectorstore.py`](Integration/conversation_vectorstore.py).

- Social Skill Development
  - Orchestration: [`main_controller.py`](Social%20Skill%20Development/main_controller.py).
  - Web backend: [`backend/app/main.py`](Social%20Skill%20Development/backend/app/main.py), templates & static.
  - Emotion: [`emotion_detection/real_time_emotion.py`](Social%20Skill%20Development/emotion_detection/real_time_emotion.py).
  - TTS: [`text_to_speech/realtime_tts.py`](Social%20Skill%20Development/text_to_speech/realtime_tts.py), [`text_to_speech/main.py`](Social%20Skill%20Development/text_to_speech/main.py).
  - STT and transcription: [`video_to_text/video_to_text.py`](Social%20Skill%20Development/video_to_text/video_to_text.py), [`video_to_text/realtime_stt.py`](Social%20Skill%20Development/video_to_text/realtime_stt.py).

## Setup

Prerequisites:
- Python 3.10+ recommended.
- ffmpeg (needed for Whisper transcription). macOS: `brew install ffmpeg`, Ubuntu: `sudo apt-get install ffmpeg`.

Create a virtual environment:
- macOS/Linux:
  ```sh
  python3 -m venv .venv
  source .venv/bin/activate
  ```
- Windows (PowerShell):
  ```sh
  py -m venv .venv
  .\.venv\Scripts\Activate.ps1
  ```

Install main dependencies:
```sh
pip install -r Integration/requirements.txt
```

Component-specific extras:
```sh
# Emotional Chatbot (if running standalone)
pip install -r Integration/Emotional\ Chatbot/backend/app/requirements.txt  # if present

# Learning Platform backend extras
pip install -r Integration/Learning\ Platform/backend/requirements.txt      # if present

# Social Skill Development (root requirements)
pip install -r Social\ Skill\ Development/requirements.txt

# Social TTS/STT specific
pip install -r Social\ Skill\ Development/text_to_speech/requirements.txt
pip install -r Social\ Skill\ Development/video_to_text/requirements.txt
```

## How to Run

Run components in separate VS Code terminals as needed.

- Emotional Support Chatbot (CLI):
  ```sh
  cd Integration/Emotional\ Chatbot
  python main.py
  ```
  Uses logging via [`logger.py`](Integration/Emotional%20Chatbot/logger.py) and stores conversations with [`log_conversation_to_store`](Integration/conversation_vectorstore.py).

- Emotional Support Chatbot (Streamlit UI):
  ```sh
  cd Integration/Emotional\ Chatbot
  streamlit run streamlit_app.py
  ```

- Learning Platform (Streamlit UI, resource search + TTS):
  ```sh
  cd Integration/Learning\ Platform
  streamlit run streamlit_app.py
  ```
  Audio generation is handled by [`generate_audio_for_streamlit`](Integration/Learning%20Platform/streamlit_app.py) using [`TTS`](Integration/Learning%20Platform/TTS.py).

- Test Generation Platform (Streamlit UI):
  ```sh
  cd Integration/Learning\ Platform\ -\ Test\ Generation
  streamlit run streamlit_app.py
  ```
  Ensure LoRA assets exist in [`llama3.2-past-lora`](Integration/Learning%20Platform%20-%20Test%20Generation/llama3.2-past-lora).

- Integration Web App (if used):
  ```sh
  cd Integration
  python app.py
  ```

- Social Skill Development — Web Backend:
  ```sh
  cd Social\ Skill\ Development/backend/app
  python main.py
  # Open http://127.0.0.1:5000
  ```

- Social Skill Development — Orchestrator:
  ```sh
  cd Social\ Skill\ Development
  python main_controller.py
  ```

- Social Skill Development — Real-time TTS:
  ```sh
  cd Social\ Skill\ Development/text_to_speech
  python main.py
  # or use the queue-backed engine: python realtime_tts.py
  ```

- Social Skill Development — Whisper Video-to-Text:
  ```sh
  cd Social\ Skill\ Development/video_to_text
  python video_to_text.py
  # requires ffmpeg and will output to output.txt
  ```

- Social Skill Development — Real-time STT (microphone):
  ```sh
  cd Social\ Skill\ Development/video_to_text
  python realtime_stt.py
  ```

## Logs
Logs are written to various `Logs/` folders, e.g., [`Integration/Logs`](Integration/Logs), and via components like [`logger.py`](Integration/Emotional%20Chatbot/logger.py).

## Security and Licensing
- Hugging Face model scripts included under their licenses in the dataset folder.
- Ensure no sensitive data is committed to logs or the FAISS index.