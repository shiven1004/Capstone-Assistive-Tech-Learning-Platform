import streamlit as st
import os
from datetime import datetime
from emotion_detection_pipeline import detect_enhanced_emotion
from generation_pipeline import generate_educational_response
from logger import Logger
from TTS import TTS
from conversation_vectorstore import log_conversation_to_store

logger = Logger(
    name="Educational ChatBot-UI",
    log_file_needed=True,
    log_file="Logs/educational_chatbot_ui.log",
    level="DEV"
)

# Initialize TTS engine
@st.cache_resource
def initialize_tts():
    """Initialize TTS engine (cached for performance)"""
    try:
        # Use gTTS since pyttsx3 is not installed
        tts = TTS(engine_name="gtts")
        logger.debug("TTS engine initialized with gTTS")
        return tts
    except Exception as e:
        logger.error(f"Failed to initialize gTTS: {e}")
        return None

tts_engine = initialize_tts()

def generate_audio_for_streamlit(text: str, response_id: int) -> str:
    """Generate audio file and return file path for Streamlit"""
    try:
        if tts_engine is None:
            raise RuntimeError("TTS engine not initialized")
        
        # Clean text for TTS processing
        clean_text = ''.join(char for char in text if ord(char) < 128 or char.isspace())
        clean_text = clean_text.strip()
        
        if not clean_text:
            raise RuntimeError("No valid text after cleaning")
        
        logger.debug(f"Cleaned text for TTS: {clean_text[:50]}...")
        
        # Create audio directory
        audio_dir = "audio_files"
        if not os.path.exists(audio_dir):
            os.makedirs(audio_dir)
        
        # Generate audio file
        audio_file = os.path.join(audio_dir, f"response_{response_id}.mp3")
        tts_engine.save(clean_text, audio_file)
        
        if os.path.exists(audio_file) and os.path.getsize(audio_file) > 0:
            logger.debug(f"Audio file generated: {audio_file}, size: {os.path.getsize(audio_file)} bytes")
            
            # Clean up old audio files (keep last 5)
            try:
                audio_files = [f for f in os.listdir(audio_dir) if f.startswith("response_") and f.endswith(".mp3")]
                if len(audio_files) > 5:
                    audio_files.sort(key=lambda x: os.path.getctime(os.path.join(audio_dir, x)))
                    for old_file in audio_files[:-5]:
                        os.unlink(os.path.join(audio_dir, old_file))
                        logger.debug(f"Cleaned up old audio file: {old_file}")
            except Exception as cleanup_error:
                logger.warning(f"Audio cleanup failed: {cleanup_error}")
            
            return audio_file
        else:
            raise RuntimeError("Audio file was not created or is empty")
            
    except Exception as e:
        logger.error(f"Error generating audio: {e}")
        raise

st.set_page_config(page_title="🎓 Educational Support Chatbot", page_icon="🎓")

if "conversation" not in st.session_state:
    st.session_state.conversation = []
if "profile" not in st.session_state:
    st.session_state.profile = {
        "session_count": 0,
        "identified_needs": set(),
        "emotional_patterns": []
    }
if "user_id" not in st.session_state:
    st.session_state.user_id = None
if "session_start" not in st.session_state:
    st.session_state.session_start = datetime.now()

with st.sidebar:
    st.title("👤 Learning Profile")
    
    # Get user ID
    if st.session_state.user_id is None:
        st.session_state.user_id = st.text_input("Enter your name or user ID:", key="user_id_input")
    else:
        st.markdown(f"**User:** {st.session_state.user_id}")
    
    profile = st.session_state.profile
    st.markdown(f"- **Sessions:** {profile['session_count']}")
    if profile["identified_needs"]:
        st.markdown(f"- **Learning patterns:** {', '.join(profile['identified_needs'])}")
    if profile["emotional_patterns"]:
        st.markdown(
            f"- **Recent emotions:** {', '.join(profile['emotional_patterns'][-5:])}"
        )

    st.markdown("---")
    with st.expander("ℹ️ Help", expanded=False):
        st.write(
            """
            • Ask me homework questions or share how you feel about studying.  
            • Tell me if you have dyslexia, ADHD, or other learning differences.  
            • Be specific about what's confusing or frustrating you.  
            • Every question is a good question—just type and hit **Enter**!
            """
        )


st.title("🎓 Emotional Support Chatbot")
st.markdown(
    "Hello! I'm your AI learning companion. Ask anything about schoolwork or how you're feeling about learning."
)

for idx, turn in enumerate(st.session_state.conversation):
    with st.chat_message("user"):
        st.markdown(turn["user"])
    with st.chat_message("assistant"):
        st.markdown(turn["bot"])
        
        # Add audio player for bot response
        if tts_engine:
            try:
                audio_file = generate_audio_for_streamlit(turn["bot"], idx)
                
                if os.path.exists(audio_file):
                    with open(audio_file, 'rb') as f:
                        st.audio(f.read(), format='audio/mpeg')
                    logger.debug(f"Audio displayed for response {idx}")
                else:
                    st.warning("⚠️ Audio file not found")
                    
            except Exception as e:
                logger.error(f"Error generating audio for response {idx}: {e}")
                st.warning("⚠️ Could not generate audio. Check internet connection.")
        else:
            st.info("ℹ️ TTS engine not available")
        
        # Display emotion analysis
        emo = turn["emotion"]
        st.caption(
            f"🧠 *Detected:* {emo['primary_emotion'].title()} "
            f"({emo['confidence']:.0%}) — {emo['educational_context']}"
        )

user_input = st.chat_input("Type your question or feeling …")

if user_input and st.session_state.user_id:
    logger.debug(f"User: {user_input}")

    emotion = detect_enhanced_emotion(
        user_input,
        {
            "conversation_history": st.session_state.conversation[-3:],
            "student_profile": st.session_state.profile,
        },
    )

    bot_reply = generate_educational_response(user_input, emotion)

    st.session_state.conversation.append(
        {"user": user_input, "bot": bot_reply, "emotion": emotion}
    )
    profile = st.session_state.profile
    profile["session_count"] += 1
    profile["emotional_patterns"].append(emotion["primary_emotion"])
    if emotion["educational_context"] != "general":
        profile["identified_needs"].add(emotion["educational_context"])
    for ind in emotion["special_needs_indicators"]:
        profile["identified_needs"].add(ind)
    
    # Log conversation to vectorstore
    try:
        conversation_messages = []
        for turn in st.session_state.conversation:
            conversation_messages.append({"role": "user", "content": turn["user"]})
            conversation_messages.append({"role": "assistant", "content": turn["bot"]})
        
        conversation = {
            "messages": conversation_messages,
            "timestamp": st.session_state.session_start.isoformat()
        }
        log_conversation_to_store(conversation, "emotional", st.session_state.user_id)
        logger.debug(f"Logged {len(conversation_messages)} messages to vectorstore")
    except Exception as e:
        logger.error(f"Error logging conversation: {e}")

    st.rerun()
elif user_input and not st.session_state.user_id:
    st.warning("Please enter your user ID first!")
