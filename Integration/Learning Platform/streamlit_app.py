import json
import random
import re
from ddgs import DDGS
import streamlit as st
from academic_generation_pipeline import get_chat_response, get_model_handler
from TTS import TTS
from logger import Logger
from datetime import datetime
from conversation_vectorstore import log_conversation_to_store
import os

# Initialize logger for Streamlit app
log_dir = os.path.join(os.path.dirname(__file__), "Logs")
os.makedirs(log_dir, exist_ok=True)
app_logger = Logger(
    name="StreamlitApp",
    log_file_needed=True,
    log_file=os.path.join(log_dir, "streamlit_app.log"),
    level="DEV"
)
GRADES = ["Grade 1", "Grade 2", "Grade 3", "Grade 4", "Grade 5"]
SUBJECTS = ["English", "Maths", "Science"]
BANNED_DOMAINS = ["reddit.com", "quora.com", "pinterest.com", "facebook.com", "x.com", "twitter.com"]
BANNED_KEYWORDS = ["adult", "porn", "violence", "gun", "gambling"]
NUM_LINKS = 4

TOPICS = {
    "English": ["reading comprehension", "grammar basics", "synonyms", "short stories", "punctuation", "poetry", "writing skills"],
    "Maths": ["fractions", "multiplication", "place value", "time", "word problems", "geometry", "algebra basics"],
    "Science": ["states of matter", "plants", "solar system", "energy", "food chain", "water cycle", "human body"],
}
ENGLISH_STOP = {"the","is","are","and","to","in","for","with","from","this","that","of","on","it","as","by","an","be","at"}

# Initialize TTS engine (cached for performance)
@st.cache_resource
def initialize_tts():
    """Initialize TTS engine (cached for performance)"""
    try:
        tts = TTS(engine_name="gtts")
        app_logger.info("TTS engine initialized successfully with gTTS")
        return tts
    except Exception as e:
        app_logger.error(f"Failed to initialize TTS engine: {str(e)}")
        return None

tts_engine = initialize_tts()

def generate_audio_for_streamlit(text: str, response_id: int) -> str:
    """Generate audio file and return file path for Streamlit"""
    try:
        if tts_engine is None:
            raise RuntimeError("TTS engine not initialized")
        
        # Clean text for TTS processing (remove non-ASCII characters)
        clean_text = ''.join(char for char in text if ord(char) < 128 or char.isspace())
        clean_text = clean_text.strip()
        
        if not clean_text:
            raise RuntimeError("No valid text after cleaning")
        
        app_logger.debug(f"Cleaned text for TTS: {clean_text[:50]}...")
        
        # Create audio directory
        audio_dir = "audio_files"
        if not os.path.exists(audio_dir):
            os.makedirs(audio_dir)
        
        # Generate audio file
        audio_file = os.path.join(audio_dir, f"response_{response_id}.mp3")
        tts_engine.save(clean_text, audio_file)
        
        if os.path.exists(audio_file) and os.path.getsize(audio_file) > 0:
            app_logger.debug(f"Audio file generated: {audio_file}, size: {os.path.getsize(audio_file)} bytes")
            
            # Clean up old audio files (keep last 5)
            try:
                audio_files = [f for f in os.listdir(audio_dir) if f.startswith("response_") and f.endswith(".mp3")]
                if len(audio_files) > 5:
                    audio_files.sort(key=lambda x: os.path.getctime(os.path.join(audio_dir, x)))
                    for old_file in audio_files[:-5]:
                        os.unlink(os.path.join(audio_dir, old_file))
                        app_logger.debug(f"Cleaned up old audio file: {old_file}")
            except Exception as cleanup_error:
                app_logger.warning(f"Audio cleanup failed: {cleanup_error}")
            
            return audio_file
        else:
            raise RuntimeError("Audio file was not created or is empty")
            
    except Exception as e:
        app_logger.error(f"Error generating audio: {e}")
        raise

# Web Search Functions
def ddg_search(query, max_results=6):
    out = []
    try:
        with DDGS(timeout=8) as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                out.append({"title": r.get("title") or "", "url": r.get("href") or "", "snippet": r.get("body") or ""})
    except Exception as e:
        app_logger.warning(f"DuckDuckGo search failed: {str(e)}")
        pass
    return out

def basic_prefilter(results):
    clean = []
    for r in results:
        u = r["url"].lower()
        t = (r["title"] + " " + r["snippet"]).lower()
        if any(d in u for d in BANNED_DOMAINS):
            continue
        if any(k in t for k in BANNED_KEYWORDS):
            continue
        if not is_english(r["title"] + " " + r["snippet"]):
            continue
        clean.append(r)
    app_logger.debug(f"Pre-filtered {len(results)} results to {len(clean)} clean results")
    return clean

def is_english(text):
    txt = re.sub(r"[^a-zA-Z\s]"," ", text)
    words = [w for w in txt.lower().split() if w]
    if not words:
        return False
    stop_hits = sum(1 for w in words if w in ENGLISH_STOP)
    ascii_ratio = sum(c.isascii() for c in text) / max(1,len(text))
    return ascii_ratio > 0.95 and stop_hits >= 2

def simple_score_resource(result, subject, topic):
    """Score resource based on keyword matching"""
    text = (result["title"] + " " + result["snippet"]).lower()
    score = 0
    
    # Keyword bonuses
    kid_words = ["kids", "children", "student", "learn", "worksheet", "lesson", "activity", "game", "practice"]
    for word in kid_words:
        if word in text:
            score += 2
    
    # Subject/topic match
    if subject.lower() in text:
        score += 3
    if topic.lower() in text:
        score += 3
    
    # Educational domains
    edu_domains = ["edu", "education", "learning", "teach", "school", "Khan", "BBC"]
    for domain in edu_domains:
        if domain.lower() in result["url"].lower():
            score += 5
    
    return score

def rerank_kid_friendly(results, grade, subject, topic):
    """Fast scoring-based filtering instead of slow AI reranking"""
    if not results:
        return []
    
    scored = [(simple_score_resource(r, subject, topic), r) for r in results]
    scored.sort(reverse=True, key=lambda x: x[0])
    
    top = [r for _, r in scored[:NUM_LINKS]]
    
    # Add simple type classification
    for item in top:
        title_lower = item["title"].lower()
        if "video" in title_lower or "youtube" in item["url"].lower():
            item["type"] = "video"
        elif "worksheet" in title_lower or "pdf" in item["url"].lower():
            item["type"] = "worksheet"
        elif "game" in title_lower or "play" in title_lower:
            item["type"] = "game"
        else:
            item["type"] = "notes"
        item["why_short"] = f"Relevant {subject} resource for {topic}"
    
    return top

def build_query(grade, subject, topic):
    return f"{grade} {subject} '{topic}' lesson for kids worksheet video"

def fetch_resources_for_subject(grade, subject):
    """Fetch learning resources for a specific subject and grade"""
    topic = random.choice(TOPICS[subject])
    q = build_query(grade, subject, topic)
    app_logger.info(f"Fetching resources for {grade} {subject} - Topic: {topic}")
    raw = basic_prefilter(ddg_search(q, 6))
    if not raw:
        app_logger.warning(f"No resources found for {subject} - {topic}")
        return {"subject": subject, "topic": topic, "grade": grade, "links": []}
    picked = rerank_kid_friendly(raw, grade, subject, topic)
    app_logger.info(f"Found {len(picked)} resources for {grade} {subject}")
    return {"subject": subject, "topic": topic, "grade": grade, "links": picked}

def main():
    st.set_page_config(page_title="Learning Platform", page_icon="📚", layout="wide")
    
    app_logger.info("Learning Platform application started")
    
    # Custom CSS
    st.markdown("""
        <style>
        .block-container { padding-top: 2rem; padding-bottom: 2rem; }
        .main > div { padding: 1.25rem 2.5rem; }
        .stButton button { height: 2.6rem; font-size: 0.95rem; padding: 0.3rem 0.85rem; }
        h1 { font-size: 2rem !important; margin: 0 0 0.6rem 0 !important; }
        h2 { font-size: 1.3rem !important; margin: 0.6rem 0 !important; }
        h3 { font-size: 1.1rem !important; }
        .stMarkdown p { margin-bottom: 0.6rem !important; }
        /* Chat bubbles - darker, better contrast on dark theme */
        .chat-message { padding: 0.9rem; border-radius: 12px; margin-bottom: 0.9rem; border: 1px solid #2a2a2a; color: #e5e7eb; }
        .user-message { background-color: rgba(37,99,235,0.15); text-align: right; }
        .bot-message { background-color: rgba(255,255,255,0.06); }
        /* Chat input blending */
        [data-testid="stChatInput"] input { background-color: #0f172a; color: #e5e7eb; border-radius: 10px; border: 1px solid #334155; }
        [data-testid="stChatInput"] input::placeholder { color: #94a3b8; }
        </style>
    """, unsafe_allow_html=True)
    
    # Initialize session state
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    if 'search_results' not in st.session_state:
        st.session_state.search_results = None
    if 'user_id' not in st.session_state:
        st.session_state.user_id = None
    if 'session_start' not in st.session_state:
        st.session_state.session_start = datetime.now()
    
    # Main title
    st.title("🎓 Learning Platform")
    
    # Get user ID in sidebar
    with st.sidebar:
        st.title("👤 User Profile")
        if st.session_state.user_id is None:
            st.session_state.user_id = st.text_input("Enter your name or user ID:", key="user_id_input")
        else:
            st.markdown(f"**User:** {st.session_state.user_id}")
        
        # Display chat statistics
        if st.session_state.chat_history:
            st.markdown("---")
            st.markdown(f"**Messages:** {len(st.session_state.chat_history)}")
            user_msgs = sum(1 for m in st.session_state.chat_history if m['role'] == 'user')
            st.markdown(f"**Questions asked:** {user_msgs}")
    
    
    # Split screen layout
    left_col, right_col = st.columns([3, 2])
    
    # LEFT SIDE - Academic Chatbot
    with left_col:
        st.header("💬 Academic Chat Assistant")
        st.markdown("*Ask me anything about your studies!*")
        
        # Chat history display
        chat_container = st.container()
        with chat_container:
            if st.session_state.chat_history:
                for idx, message in enumerate(st.session_state.chat_history):
                    if message['role'] == 'user':
                        st.markdown(f"""
                        <div class="chat-message user-message">
                            <strong>You:</strong> {message['content']}
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div class="chat-message bot-message">
                            <strong>🤖 Assistant:</strong> {message['content']}
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Display audio player if available for this response
                        if tts_engine:
                            try:
                                audio_file = generate_audio_for_streamlit(message['content'], idx)
                                if os.path.exists(audio_file):
                                    with open(audio_file, 'rb') as f:
                                        st.audio(f.read(), format='audio/mpeg')
                                    app_logger.debug(f"Audio displayed for response {idx}")
                                else:
                                    st.warning("⚠️ Audio file not found")
                            except Exception as e:
                                app_logger.error(f"Error generating audio for response {idx}: {e}")
                                st.warning("⚠️ Could not generate audio. Check internet connection.")
                        else:
                            st.info("ℹ️ TTS engine not available")
            else:
                st.empty()
        
        # Chat input (Enter to send) + clear button
        c1, c2 = st.columns([6, 1])
        with c2:
            if st.button("🗑️ Clear", use_container_width=True):
                # Save conversation before clearing
                if st.session_state.chat_history and st.session_state.user_id:
                    try:
                        conversation = {
                            "messages": st.session_state.chat_history,
                            "timestamp": st.session_state.session_start.isoformat()
                        }
                        log_conversation_to_store(conversation, "learning", st.session_state.user_id)
                        app_logger.info(f"Saved {len(st.session_state.chat_history)} messages to vectorstore before clearing")
                        st.success("💾 Conversation saved!")
                    except Exception as e:
                        app_logger.error(f"Error saving conversation: {e}")
                
                st.session_state.chat_history = []
                st.session_state.session_start = datetime.now()
                app_logger.info("Chat history cleared by user")
                st.rerun()
        
        user_input = st.chat_input("Type your question and press Enter…")
        if user_input and st.session_state.user_id:
            app_logger.info(f"User question: {user_input[:100]}")
            st.session_state.chat_history.append({'role': 'user', 'content': user_input.strip()})
            with st.spinner("🤔 Thinking..."):
                bot_response = get_chat_response(user_input.strip(), st.session_state.chat_history)
            app_logger.info(f"Assistant response generated: {bot_response[:100]}")
            st.session_state.chat_history.append({'role': 'assistant', 'content': bot_response})
            
            # Save conversation to vectorstore after each message
            try:
                conversation = {
                    "messages": st.session_state.chat_history,
                    "timestamp": st.session_state.session_start.isoformat()
                }
                log_conversation_to_store(conversation, "learning", st.session_state.user_id)
                app_logger.debug(f"Logged {len(st.session_state.chat_history)} messages to vectorstore")
            except Exception as e:
                app_logger.error(f"Error logging conversation: {e}")
            
            app_logger.info("Audio generation handled in display phase")
            st.rerun()
        elif user_input and not st.session_state.user_id:
            st.warning("Please enter your user ID first!")
    
    # RIGHT SIDE - Resource Search
    with right_col:
        st.header("🔍 Learning Resources")
        st.markdown("*Find educational materials for your subjects*")
        
        # Selection form
        with st.form(key='search_form'):
            col1, col2 = st.columns(2)
            
            with col1:
                selected_grade = st.selectbox("Select Grade:", GRADES, index=2)
            
            with col2:
                selected_subject = st.selectbox("Select Subject:", SUBJECTS)
            
            search_button = st.form_submit_button("🔎 Search Resources", use_container_width=True, type="primary")
            
            if search_button:
                app_logger.info(f"Resource search initiated for {selected_grade} - {selected_subject}")
                with st.spinner(f"Searching for {selected_subject} resources for {selected_grade}..."):
                    results = fetch_resources_for_subject(selected_grade, selected_subject)
                    st.session_state.search_results = results
                st.success(f"✅ Found resources for {selected_subject}!")
        
        # Display search results
        if st.session_state.search_results:
            results = st.session_state.search_results
            
            st.markdown("---")
            
            # Subject emoji mapping
            emoji_map = {"English": "📖", "Maths": "🔢", "Science": "🔬"}
            
            st.subheader(f"{emoji_map.get(results['subject'], '📚')} {results['subject']}")
            st.markdown(f"**Grade:** {results['grade']}")
            st.markdown(f"**Topic:** *{results['topic']}*")
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            if not results['links']:
                st.warning("⚠️ No resources found. Try another search!")
                app_logger.warning(f"No resources found for {results['subject']} - {results['topic']}")
            else:
                st.success(f"📚 Found {len(results['links'])} resources:")
                
                # Display links as buttons
                for idx, link in enumerate(results['links'], 1):
                    title = link.get("title", "Resource")
                    url = link.get("url", "#")
                    resource_type = link.get("type", "other").capitalize()
                    
                    # Button with title
                    button_label = f"{idx}. {resource_type}: {title[:45]}..."
                    st.link_button(button_label, url)
                    
                    # Show why this resource was selected
                    why = link.get("why_short", "")
                    if why:
                        with st.expander(f"ℹ️ Why resource {idx}?"):
                            st.write(why)
        else:
            st.empty()

if __name__ == "__main__":
    main()
