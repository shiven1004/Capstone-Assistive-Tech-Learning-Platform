KEYWORDS = [
    "help", "ask", "step", "first", "then",
    "try", "again", "break", "robot", "clean",
    "emotion", "feel", "happy", "sad", "angry"
]

def score_answer(answer):
    answer = answer.lower()
    score = 0

    for word in KEYWORDS:
        if word in answer:
            score += 1

    return score
