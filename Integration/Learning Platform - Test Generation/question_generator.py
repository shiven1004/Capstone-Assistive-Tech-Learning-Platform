from model_handler import ModelHandler
from transformers.pipelines import pipeline
from langchain_huggingface import HuggingFacePipeline
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from peft import PeftModel, PeftConfig
from logger import Logger
import warnings
import os
import re
import time
import torch

warnings.filterwarnings("ignore")

LOG = Logger("Test Generator Logger", log_file_needed=True, log_file_path="Logs/test_generator.log", level='DEV')

def is_book_author_question(question_text: str) -> bool:
    """Check if question is about book authors - filter these out"""
    keywords = [
        'author',
        'wrote',
        'written by',
        'who wrote',
        'who is the author',
        'book',
        'novel',
        'poem',
        'wrote the',
        'author of'
    ]
    text_lower = question_text.lower()
    return any(keyword in text_lower for keyword in keywords)


def _ensure_single_correct_marker(choices):
    """Guarantee exactly one [CORRECT] marker; default to first choice if missing."""
    if not choices:
        return choices
    marked_indices = [idx for idx, c in enumerate(choices) if '[CORRECT]' in c]
    if len(marked_indices) == 1:
        return choices
    # Remove all markers
    cleaned = [c.replace(' [CORRECT]', '') for c in choices]
    # If none were marked, mark the first; if multiple, keep the first as correct
    cleaned[0] = cleaned[0] + " [CORRECT]"
    return cleaned

MODEL_ID = "meta-llama/Llama-3.2-3B-Instruct"
QUANTIZE = False


if torch.backends.mps.is_available():
    DEVICE = torch.device("mps")
else:
    DEVICE = torch.device("cpu")


handler = ModelHandler(model_id=MODEL_ID, quantize=QUANTIZE)
base_model, tokenizer = handler.load_model()

if os.path.exists("llama3.2-past-lora"):
    try:
        config = PeftConfig.from_pretrained("llama3.2-past-lora")
        model = PeftModel.from_pretrained(base_model, "llama3.2-past-lora", config=config, is_trainable=False)
        model = model.merge_and_unload()
        LOG.debug("PEFT adapter loaded successfully")
    except Exception as e:
        LOG.error(f"Error loading PEFT adapter: {e}")
        model = base_model
else:
    LOG.debug("PEFT adapter not found, using base model")
    model = base_model

# Ensure model lives on the chosen device
model = model.to(DEVICE)

pipe = pipeline(
    "text-generation",
    model=model,
    tokenizer=tokenizer,
    max_new_tokens=2000,
    do_sample=True,
    temperature=0.4,
    top_p=0.9,
    top_k=50,
    repetition_penalty=1.1,
    eos_token_id=tokenizer.eos_token_id,
    pad_token_id=tokenizer.eos_token_id,
    return_full_text=False,
    device=0,
)

# Export pipeline for evaluation module to reuse
def get_pipeline():
    """Return the loaded pipeline for reuse in other modules"""
    return pipe

# Initialize evaluation module with the loaded pipeline
try:
    from evaluation_module import set_pipeline
    set_pipeline(pipe)
except ImportError:
    pass

def create_enhanced_prompts():
    """Simplified prompts for better LLM generation"""
    return {
    "Phonological Awareness": """Generate 5 phonological awareness questions for young learners.

Format for EACH question:
1. Question text?
a) plausible choice
b) correct answer [CORRECT]
c) plausible choice
d) plausible choice

Rules:
- Exactly ONE choice must include [CORRECT]
- All choices must be plausible, simple words or syllable counts
- No explanations or extra text

Example:
1. What is the word "feet" without /f/?
a) beat
b) eet [CORRECT]
c) feet
d) eat

Return ONLY 5 numbered questions (1-5) in plain text.
Now generate:""",

    "Mathematics": """Generate 5 basic math questions.

Format for EACH question:
1. Question text?
a) numeric choice
b) correct answer [CORRECT]
c) numeric choice
d) numeric choice

Rules:
- Exactly ONE choice must include [CORRECT]
- All choices must be numbers
- Use simple arithmetic for K-3

Example:
1. What is 3 + 2?
a) 4
b) 5 [CORRECT]
c) 6
d) 3

Return ONLY 5 numbered questions (1-5) in plain text.
Now generate:""",

    "Science": """Generate 5 simple science questions.

Format for EACH question:
1. Question text?
a) plausible choice
b) correct answer [CORRECT]
c) plausible choice
d) plausible choice

Rules:
- Exactly ONE choice must include [CORRECT]
- Choices must be real, related concepts

Example:
1. Which animal says 'meow'?
a) dog
b) cat [CORRECT]
c) bird
d) cow

Return ONLY 5 numbered questions (1-5) in plain text.
Now generate:""",

    "General Knowledge": """Generate 5 general knowledge questions.

Format for EACH question:
1. Question text?
a) plausible choice
b) correct answer [CORRECT]
c) plausible choice
d) plausible choice

Rules:
- Exactly ONE choice must include [CORRECT]
- Keep content age-appropriate and factual

Example:
1. How many days in a week?
a) 5
b) 7 [CORRECT]
c) 6
d) 8

Return ONLY 5 numbered questions (1-5) in plain text.
Now generate:"""
    }

def create_subject_chain(subject_name):
    """Create chain for generation"""
    prompts = create_enhanced_prompts()
    template = prompts[subject_name]
    prompt = PromptTemplate.from_template(template=template)
    return prompt | HuggingFacePipeline(pipeline=pipe) | StrOutputParser()

def normalize_stem(text: str) -> str:
    """Normalize a question stem for duplicate detection"""
    s = text.strip().lower()
    s = re.sub(r'^(q(uestion)?\s*)?(\d+[\.\)\:\-]\s*)', '', s)
    s = re.sub(r'[^a-z0-9\s/]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def extract_questions_from_bulk_response(text, subject_name, target=25, seen_stems=None):
    """Extract questions with strict duplicate checking and retry logic"""
    if not text or len(text.strip()) == 0:
        return []
    
    if seen_stems is None:
        seen_stems = set()
    
    lines = text.split('\n')
    questions = []
    skipped_duplicates = 0
    i = 0
    
    while i < len(lines) and len(questions) < target:
        line = lines[i].strip()
        
        # Look for numbered questions
        question_match = re.match(r'^(\d+)\.\s*(.+)', line)
        if question_match:
            question_text = question_match.group(2).strip()
            
            # Skip if too short
            if len(question_text) < 5:
                i += 1
                continue
            
            # Check for duplicates
            stem_norm = normalize_stem(question_text)
            if stem_norm in seen_stems:
                skipped_duplicates += 1
                LOG.debug(f"Duplicate skipped for {subject_name}: {question_text[:50]}...")
                # Skip to next question
                i += 1
                while i < len(lines) and not re.match(r'^\d+\.', lines[i].strip()):
                    i += 1
                continue
            
            # Skip book author questions
            if is_book_author_question(question_text):
                LOG.debug(f"Book author question skipped for {subject_name}: {question_text[:50]}...")
                i += 1
                while i < len(lines) and not re.match(r'^\d+\.', lines[i].strip()):
                    i += 1
                continue
            
            choices = []
            j = i + 1
            
            # Collect choices
            while j < len(lines) and len(choices) < 4:
                choice_line = lines[j].strip()
                if re.match(r'^[a-d]\)\s*.+', choice_line, re.IGNORECASE):
                    choices.append(choice_line)
                    j += 1
                elif choice_line == "":
                    j += 1
                elif re.match(r'^\d+\.', choice_line):
                    break
                else:
                    j += 1
            
            if len(choices) >= 3:
                # Ensure exactly 4 choices
                while len(choices) < 4:
                    choices.append(f"{chr(97+len(choices))}) other")
                choices = _ensure_single_correct_marker(choices)
                full_question = f"{question_text}\n" + "\n".join(choices[:4])
                questions.append(full_question)
                seen_stems.add(stem_norm)
                LOG.debug(f"Added Q{len(questions)} for {subject_name}: {question_text[:50]}...")
            
            i = j
        else:
            i += 1
    
    LOG.debug(f"Extracted {len(questions)} questions, skipped {skipped_duplicates} duplicates for {subject_name}")
    return questions

def generate_individual_questions(subject_name, needed_count, seen_stems, difficulty_level="medium"):
    """Generate individual questions to fill gaps"""
    print(f"    Generating {needed_count} individual {difficulty_level} questions for {subject_name}...")
    
    difficulty_prompts = {
        "easy": "Generate 1 easy question suitable for beginners.",
        "medium": "Generate 1 medium difficulty question.",
        "hard": "Generate 1 challenging question requiring more thinking."
    }
    
    base_prompts = {
        "Phonological Awareness": f"Generate 1 phonological awareness question. {difficulty_prompts[difficulty_level]} Format: Question? a) plausible choice b) correct answer [CORRECT] c) plausible choice d) plausible choice",
        "Mathematics": f"Generate 1 basic math question. {difficulty_prompts[difficulty_level]} Format: Question? a) number b) correct number [CORRECT] c) number d) number",
        "Science": f"Generate 1 science question. {difficulty_prompts[difficulty_level]} Format: Question? a) plausible choice b) correct answer [CORRECT] c) plausible choice d) plausible choice",
        "General Knowledge": f"Generate 1 general knowledge question. {difficulty_prompts[difficulty_level]} Format: Question? a) plausible choice b) correct answer [CORRECT] c) plausible choice d) plausible choice"
    }
    
    template = base_prompts[subject_name]
    prompt = PromptTemplate.from_template(template=template)
    chain = prompt | HuggingFacePipeline(pipeline=pipe) | StrOutputParser()
    
    questions = []
    attempts = 0
    max_attempts = needed_count * 4
    
    while len(questions) < needed_count and attempts < max_attempts:
        try:
            response = chain.invoke({})
            
            if response and len(response.strip()) > 0:
                lines = response.split('\n')
                question_line = None
                choices = []
                
                for line in lines:
                    line = line.strip()
                    if '?' in line and not line.startswith(('a)', 'b)', 'c)', 'd)')):
                        question_line = line
                    elif re.match(r'^[a-d]\)', line):
                        choices.append(line)
                
                if question_line and len(choices) >= 3:
                    # Check for duplicates
                    stem_norm = normalize_stem(question_line)
                    if stem_norm not in seen_stems:
                        while len(choices) < 4:
                            choices.append(f"{chr(97+len(choices))}) other")
                        choices = _ensure_single_correct_marker(choices)
                        full_question = f"{question_line}\n" + "\n".join(choices[:4])
                        questions.append(full_question)
                        seen_stems.add(stem_norm)
                        print(f"      Individual Q{len(questions)}/{needed_count} generated")
            
            attempts += 1
            
        except Exception as e:
            attempts += 1
            continue
    
    return questions

def generate_subject_questions(subject_name, target=5, seen_stems=None, max_retries=3):
    """Generate exactly 5 questions using LLM with fallback"""
    if seen_stems is None:
        seen_stems = set()
    
    print(f"🔄 Generating {target} questions for {subject_name}...")
    
    best_questions = []
    
    for attempt in range(max_retries):
        try:
            chain = create_subject_chain(subject_name)
            response = chain.invoke({})
            
            print(f"  🔍 Attempt {attempt + 1} response length: {len(response) if response else 0}")
            if response:
                print(f"  📄 Response preview: {response[:100]}...")
            
            if response and len(response.strip()) > 0:
                questions = extract_questions_from_bulk_response(
                    response, subject_name, target=target, seen_stems=seen_stems
                )
                
                if len(questions) > len(best_questions):
                    best_questions = questions
                    print(f"  📝 Attempt {attempt + 1}: Got {len(questions)} questions")
                
                # If we got target or more, we're done
                if len(best_questions) >= target:
                    print(f"  ✅ Generated {len(best_questions)} questions for {subject_name}")
                    return best_questions[:target]
            else:
                print(f"  ⚠️ Attempt {attempt + 1}: Empty response")
            
            # Small delay between retries
            if attempt < max_retries - 1 and len(best_questions) < target:
                time.sleep(0.5)
                
        except Exception as e:
            print(f"  ❌ Attempt {attempt + 1} error: {e}")
            if attempt < max_retries - 1:
                time.sleep(0.5)
    
    # Fallback to hardcoded questions if LLM fails
    if len(best_questions) < target:
        print(f"  🔄 Filling remaining with fallback for {subject_name}")
        fallback_questions = get_fallback_questions(subject_name)
        for q in fallback_questions:
            if len(best_questions) >= target:
                break
            best_questions.append(q)
    
    if len(best_questions) >= target:
        return best_questions[:target]
    
    print(f"  ❌ Failed to reach target, returning {len(best_questions)}/{target} for {subject_name}")
    return best_questions

def get_fallback_questions(subject_name):
    """Hardcoded fallback questions when LLM fails"""
    fallback = {
        "Phonological Awareness": [
            "What is the word 'time' without /t/?\na) ime [CORRECT]\nb) time\nc) me\nd) tim",
            "Say 'bookcase' without 'book'. What word do you get?\na) case [CORRECT]\nb) book\nc) bookcase\nd) ace",
            "Do the words 'top' and 'hop' rhyme?\na) Yes [CORRECT]\nb) No\nc) Maybe\nd) Sometimes",
            "How many syllables are in 'computer'?\na) 2\nb) 3 [CORRECT]\nc) 4\nd) 1",
            "What word do these sounds make: /b/ /a/ /t/?\na) cat\nb) bat [CORRECT]\nc) hat\nd) rat"
        ],
        "Mathematics": [
            "What is 2 + 3?\na) 4\nb) 5 [CORRECT]\nc) 6\nd) 7",
            "What is 7 - 2?\na) 4\nb) 5 [CORRECT]\nc) 6\nd) 3",
            "How many sides does a triangle have?\na) 2\nb) 3 [CORRECT]\nc) 4\nd) 5",
            "What is 4 + 1?\na) 5 [CORRECT]\nb) 6\nc) 3\nd) 4",
            "Count: How many fingers on one hand?\na) 4\nb) 5 [CORRECT]\nc) 6\nd) 3"
        ],
        "Science": [
            "Which is alive?\na) rock\nb) dog [CORRECT]\nc) chair\nd) book",
            "What do plants need?\na) sugar\nb) water [CORRECT]\nc) salt\nd) metal",
            "What animal says 'meow'?\na) dog\nb) cat [CORRECT]\nc) bird\nd) fish",
            "What helps you see?\na) ear\nb) eye [CORRECT]\nc) nose\nd) mouth",
            "Where do fish live?\na) trees\nb) water [CORRECT]\nc) air\nd) ground"
        ],
        "General Knowledge": [
            "How many days in a week?\na) 5\nb) 6\nc) 7 [CORRECT]\nd) 8",
            "What color is grass?\na) blue\nb) green [CORRECT]\nc) red\nd) yellow",
            "Who helps when you're sick?\na) teacher\nb) doctor [CORRECT]\nc) cook\nd) driver",
            "How many wheels does a car have?\na) 2\nb) 3\nc) 4 [CORRECT]\nd) 5",
            "What do we use to write?\na) spoon\nb) pen [CORRECT]\nc) cup\nd) shoe"
        ]
    }
    return fallback.get(subject_name, [])

def generate_test():
    """Generate complete test with exactly 20 questions (5 per subject)"""
    subjects = ["Phonological Awareness", "Mathematics", "Science", "General Knowledge"]
    all_output = []
    question_number = 1
    total_generated = 0
    seen_stems = set()  # Fresh set for each test
    
    print("🚀 Starting LLM test generation...")
    print("🎯 Target: 20 questions (5 per subject)")
    print("")
    
    for subject_name in subjects:
        all_output.append(f"=== {subject_name.upper()} SECTION - 5 Questions ===")
        all_output.append("")
        
        questions = generate_subject_questions(
            subject_name, target=5, seen_stems=seen_stems, max_retries=3
        )
        
        # Add questions to output
        for question in questions:
            all_output.append(f"{question_number}. {question}")
            all_output.append("")
            question_number += 1
            total_generated += 1
        
        all_output.append("")
        print("")  # Add spacing between subjects
    
    print(f"🎯 Total questions generated: {total_generated}/20")
    
    if total_generated == 20:
        print(f"✅ Success: All questions generated!")
    elif total_generated >= 15:
        print(f"⚠️ Partial success: {total_generated}/20 questions generated")
    else:
        print(f"❌ Warning: Only {total_generated}/20 questions generated")
    
    return "\n".join(all_output)
