import json
import requests
import random
import re
from ddgs import DDGS
import streamlit as st

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "llama3.2:3b"
GRADE = "Grade 3"
SUBJECTS = ["English", "Maths", "Science"]
BANNED_DOMAINS = ["reddit.com", "quora.com", "pinterest.com", "facebook.com", "x.com", "twitter.com"]
BANNED_KEYWORDS = ["adult", "porn", "violence", "gun", "gambling"]
TOPICS = {
    "English": ["reading comprehension", "grammar basics", "synonyms", "short stories", "punctuation"],
    "Maths": ["fractions", "multiplication", "place value", "time", "word problems"],
    "Science": ["states of matter", "plants", "solar system", "energy", "food chain"],
}
ENGLISH_STOP = {"the","is","are","and","to","in","for","with","from","this","that","of","on","it","as","by","an","be","at"}

def ddg_search(query, max_results=8):
    out = []
    with DDGS() as ddgs:
        for r in ddgs.text(query, max_results=max_results):
            out.append({"title": r.get("title") or "", "url": r.get("href") or "", "snippet": r.get("body") or ""})
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
    return clean

def is_english(text):
    txt = re.sub(r"[^a-zA-Z\s]"," ", text)
    words = [w for w in txt.lower().split() if w]
    if not words:
        return False
    stop_hits = sum(1 for w in words if w in ENGLISH_STOP)
    ascii_ratio = sum(c.isascii() for c in text) / max(1,len(text))
    return ascii_ratio > 0.95 and stop_hits >= 2

def get_model_handler():
    global model_handler
    if model_handler is None:
        model_handler = ModelHandler(model_name="microsoft/Phi-3-mini-4k-instruct", quantize=True)
        model_handler.load_model()
    return model_handler

def ask_model(prompt):
    handler = get_model_handler()
    return handler.generate(prompt, max_new_tokens=1024, temperature=0.7, return_json=True)

def rerank_kid_friendly(results, grade, subject, topic):
    prompt = f"Select the best 3 kid-friendly {subject} resources for {grade} on {topic}. Return JSON array of objects with title,type(one of notes/video/worksheet/game/other),url,why_short. Candidates: {json.dumps(results, ensure_ascii=False)}"
    out = ask_model(prompt)
    try:
        data = json.loads(out)
        if isinstance(data, list):
            return data
    except Exception:
        pass
    return results[:3]

def build_query(grade, subject, topic):
    return f"{grade} {subject} '{topic}' lesson for kids worksheet video"

def fetch_resources():
    """Fetch learning resources for all subjects"""
    aggregated = []
    for subject in SUBJECTS:
        topic = random.choice(TOPICS[subject])
        q = build_query(GRADE, subject, topic)
        raw = basic_prefilter(ddg_search(q, 8))
        if not raw:
            aggregated.append({"subject": subject, "topic": topic, "links": []})
            continue
        picked = rerank_kid_friendly(raw, GRADE, subject, topic)
        aggregated.append({"subject": subject, "topic": topic, "links": picked})
    return {"grade": GRADE, "results": aggregated}

def main():
    st.set_page_config(page_title="Learning Platform", page_icon="📚", layout="wide")
    
    # Custom CSS for compact right-aligned layout
    st.markdown("""
        <style>
        .main > div {
            padding-left: 2rem;
            padding-right: 2rem;
        }
        .stButton button {
            height: 2.5rem;
            font-size: 0.9rem;
            padding: 0.25rem 0.75rem;
        }
        h1 {
            font-size: 2rem !important;
            margin-bottom: 0.5rem !important;
        }
        h2 {
            font-size: 1.3rem !important;
            margin-top: 1rem !important;
            margin-bottom: 0.5rem !important;
        }
        h3 {
            font-size: 1.1rem !important;
        }
        .stMarkdown p {
            margin-bottom: 0.5rem !important;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Fetch resources only once on page load
    if 'resources' not in st.session_state:
        with st.spinner("Loading educational resources..."):
            st.session_state.resources = fetch_resources()
    
    data = st.session_state.resources
    
    # Create layout: empty left column, content on right
    col_left, col_right = st.columns([2, 2])
    
    with col_right:
        st.title("🎓 Learning Platform")
        st.markdown(f"*Educational Resources for {GRADE}*")
        
        # Subject emoji mapping
        emoji_map = {"English": "📖", "Maths": "🔢", "Science": "🔬"}
        
        # Display all three subjects in compact form
        for subject_data in data["results"]:
            subject = subject_data["subject"]
            topic = subject_data["topic"]
            links = subject_data["links"]
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.subheader(f"{emoji_map.get(subject, '📚')} {subject}")
            st.markdown(f"**{topic}**")
            
            if not links:
                st.caption("No resources found")
            else:
                # Display links as compact buttons
                for idx, link in enumerate(links):
                    title = link.get("title", "Resource")
                    url = link.get("url", "#")
                    resource_type = link.get("type", "other").capitalize()
                    
                    # Compact button with title
                    button_label = f"{resource_type}: {title[:45]}"
                    st.link_button(button_label, url)

if __name__ == "__main__":
    main()
