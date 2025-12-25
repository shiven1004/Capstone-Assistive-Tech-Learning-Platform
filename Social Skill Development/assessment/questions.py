import random

QUESTIONS = [

    # ===================== TEXT-ONLY QUESTIONS =====================

    {
        "type": "text",
        "question": "If you were a superhero, what would your special power be and what would you need help with?",
        "skills": ["self_expression", "confidence", "reasoning"],
        "image": None
    },

    {
        "type": "text",
        "question": "Imagine you are teaching a younger student how to play your favorite game. What are the first three steps?",
        "skills": ["sequencing", "working_memory"],
        "image": None
    },

    {
        "type": "text",
        "question": "If your teacher is speaking too fast and you miss the instructions, what would you do?",
        "skills": ["self_advocacy", "problem_solving"],
        "image": None
    },

    {
        "type": "text",
        "question": "Tell me about a time when something you were doing did not work. What did you do then?",
        "skills": ["emotional_regulation", "resilience"],
        "image": None
    },

    {
        "type": "text",
        "question": "If you could build a robot to help you with one boring task, what would it do?",
        "skills": ["creativity", "verbal_fluency"],
        "image": None
    },

    # ===================== IMAGE-BASED QUESTIONS =====================

    {
        "type": "image",
        "question": "Look at this picture and tell me what you think is happening.",
        "skills": ["visual_processing", "narrative"],
        "image": "assessment/images/park_scene.png"
    },

    {
        "type": "image",
        "question": "Describe everything you notice in this image.",
        "skills": ["attention_to_detail", "vocabulary"],
        "image": "assessment/images/classroom.png"
    },

    {
        "type": "image",
        "question": "How do you think the person in this picture is feeling and why?",
        "skills": ["emotion_recognition", "empathy"],
        "image": "assessment/images/emotion_face.png"
    },

    {
        "type": "image",
        "question": "Which thing in this image looks different from the others?",
        "skills": ["visual_discrimination"],
        "image": "assessment/images/odd_one_out.png"
    },

    {
        "type": "image",
        "question": "What do you think will happen next in this picture?",
        "skills": ["prediction", "logic"],
        "image": "assessment/images/cause_effect.png"
    }
]


def get_random_question():
    """
    Returns:
    {
        type: 'text' | 'image',
        question: str,
        skills: list,
        image: path or None
    }
    """
    return random.choice(QUESTIONS)
