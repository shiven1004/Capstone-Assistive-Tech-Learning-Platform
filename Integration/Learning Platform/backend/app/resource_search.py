import random
from typing import Dict, List
from logger import Logger

logger = Logger(name="FastAPI-ResourceSearch", log_file_needed=True, log_file='Logs/fastapi_resource_search.log', level='DEV')

GRADES = ["Grade 1", "Grade 2", "Grade 3", "Grade 4", "Grade 5"]
SUBJECTS = ["English", "Maths", "Science"]
NUM_LINKS = 4

CURATED_TOPICS: Dict[str, List[str]] = {
    "English": ["reading comprehension", "storytelling", "grammar practice"],
    "Maths": ["number sense", "fractions", "word problems"],
    "Science": ["space", "plants", "simple machines"],
}

CURATED_RESOURCES: Dict[str, List[Dict[str, str]]] = {
    "English": [
        {"title": "Khan Academy: Reading & Language Arts", "url": "https://www.khanacademy.org/ela", "type": "notes", "why_short": "Structured reading practice with short lessons."},
        {"title": "Storyline Online: Read-Aloud Library", "url": "https://www.storylineonline.net/", "type": "video", "why_short": "Read-aloud videos to build listening and comprehension."},
        {"title": "CommonLit: Short Stories", "url": "https://www.commonlit.org/en/library", "type": "worksheet", "why_short": "Printable passages with questions for practice."},
        {"title": "Grammar Bytes: Basics", "url": "https://chompchomp.com/exercises.htm", "type": "practice", "why_short": "Quick grammar exercises with instant feedback."},
    ],
    "Maths": [
        {"title": "Khan Academy: Early Math", "url": "https://www.khanacademy.org/math/early-math", "type": "notes", "why_short": "Short concept videos and practice for core skills."},
        {"title": "Math Playground: Games", "url": "https://www.mathplayground.com/", "type": "game", "why_short": "Interactive games that reinforce arithmetic and logic."},
        {"title": "CK-12: Elementary Math", "url": "https://www.ck12.org/student/", "type": "practice", "why_short": "Practice sets with hints for common topics."},
        {"title": "IXL Skills Practice", "url": "https://www.ixl.com/math/", "type": "worksheet", "why_short": "Targeted drills by topic with progress tracking."},
    ],
    "Science": [
        {"title": "National Geographic Kids", "url": "https://kids.nationalgeographic.com/", "type": "notes", "why_short": "Articles and visuals that explain science topics simply."},
        {"title": "NASA Space Place", "url": "https://spaceplace.nasa.gov/", "type": "game", "why_short": "Space-themed games and explainers for kids."},
        {"title": "Mystery Science Mini-Lessons", "url": "https://mysterydoug.com/", "type": "video", "why_short": "Short explorations that answer curious questions."},
        {"title": "BBC Bitesize: Primary Science", "url": "https://www.bbc.co.uk/bitesize/subjects/z2pfb9q", "type": "notes", "why_short": "Bite-sized lessons with recap quizzes."},
    ],
}


def fetch_resources_for_subject(grade: str, subject: str) -> Dict:
    topic = random.choice(CURATED_TOPICS.get(subject, ["core skills"]))
    links = CURATED_RESOURCES.get(subject, [])[:NUM_LINKS]
    logger.info(f"Returning curated resources for {grade} {subject} - Topic: {topic}")
    return {"subject": subject, "topic": topic, "grade": grade, "links": links}
