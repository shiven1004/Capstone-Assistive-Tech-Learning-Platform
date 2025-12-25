import re
import random
from typing import List, Dict
from ddgs import DDGS
from logger import Logger

logger = Logger(name="FastAPI-ResourceSearch", log_file_needed=True, log_file='Logs/fastapi_resource_search.log', level='DEV')

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


def ddg_search(query: str, max_results: int = 6) -> List[Dict]:
    out = []
    try:
        with DDGS(timeout=8) as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                out.append({"title": r.get("title") or "", "url": r.get("href") or "", "snippet": r.get("body") or ""})
    except Exception as e:
        logger.warning(f"DuckDuckGo search failed: {str(e)}")
    return out


def is_english(text: str) -> bool:
    txt = re.sub(r"[^a-zA-Z\s]"," ", text)
    words = [w for w in txt.lower().split() if w]
    if not words:
        return False
    stop_hits = sum(1 for w in words if w in ENGLISH_STOP)
    ascii_ratio = sum(c.isascii() for c in text) / max(1,len(text))
    return ascii_ratio > 0.95 and stop_hits >= 2


def basic_prefilter(results: List[Dict]) -> List[Dict]:
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
    logger.debug(f"Pre-filtered {len(results)} results to {len(clean)} clean results")
    return clean


def simple_score_resource(result: Dict, subject: str, topic: str) -> int:
    text = (result["title"] + " " + result["snippet"]).lower()
    score = 0
    kid_words = ["kids", "children", "student", "learn", "worksheet", "lesson", "activity", "game", "practice"]
    for word in kid_words:
        if word in text:
            score += 2
    if subject.lower() in text:
        score += 3
    if topic.lower() in text:
        score += 3
    edu_domains = ["edu", "education", "learning", "teach", "school", "khan", "bbc"]
    for domain in edu_domains:
        if domain.lower() in result["url"].lower():
            score += 5
    return score


def rerank_kid_friendly(results: List[Dict], grade: str, subject: str, topic: str) -> List[Dict]:
    if not results:
        return []
    scored = [(simple_score_resource(r, subject, topic), r) for r in results]
    scored.sort(reverse=True, key=lambda x: x[0])
    top = [r for _, r in scored[:NUM_LINKS]]
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


def build_query(grade: str, subject: str, topic: str) -> str:
    return f"{grade} {subject} '{topic}' lesson for kids worksheet video"


def fetch_resources_for_subject(grade: str, subject: str) -> Dict:
    topic = random.choice(TOPICS[subject])
    q = build_query(grade, subject, topic)
    logger.info(f"Fetching resources for {grade} {subject} - Topic: {topic}")
    raw = basic_prefilter(ddg_search(q, 6))
    if not raw:
        logger.warning(f"No resources found for {subject} - {topic}")
        return {"subject": subject, "topic": topic, "grade": grade, "links": []}
    picked = rerank_kid_friendly(raw, grade, subject, topic)
    logger.info(f"Found {len(picked)} resources for {grade} {subject}")
    return {"subject": subject, "topic": topic, "grade": grade, "links": picked}
