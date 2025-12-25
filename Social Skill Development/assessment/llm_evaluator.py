from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
import re

# LLM MODEL
MODEL_NAME = "meta-llama/Llama-3.2-1B-Instruct"

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForCausalLM.from_pretrained(MODEL_NAME)


def clean_markdown(text):
    """
    Remove or convert markdown formatting for clean display
    """
    # Remove bold markers ** **
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    # Remove italic markers * *
    text = re.sub(r'\*(.*?)\*', r'\1', text)
    # Remove underline markers _ _
    text = re.sub(r'_(.*?)_', r'\1', text)
    # Remove heading markers #
    text = re.sub(r'^#+\s+', '', text, flags=re.MULTILINE)
    # Clean up excessive whitespace
    text = re.sub(r'\n\n+', '\n', text)
    return text.strip()


def evaluate_with_llm(question, skills, student_answer):
    """
    LLM-based gentle evaluation for ADHD & Dyslexia students
    """

    prompt = f"""
You are a kind educational evaluator for students with ADHD and dyslexia.

Question:
{question}

Skills being observed:
{", ".join(skills)}

Student Answer:
{student_answer}

Give gentle, encouraging feedback.
Focus on clarity, relevance, and confidence.
Do NOT say the answer is wrong.
Keep the feedback short.
"""

    inputs = tokenizer(prompt, return_tensors="pt", truncation=True)

    # Ensure pad token is set for generation on causal models
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=80,
            do_sample=True,
            temperature=0.7,
            pad_token_id=tokenizer.pad_token_id,
        )

    # Decode only tokens generated beyond the prompt
    generated = outputs[0]
    prompt_len = inputs["input_ids"].shape[1]
    feedback = tokenizer.decode(generated[prompt_len:], skip_special_tokens=True)
    
    # Clean up markdown formatting
    cleaned_feedback = clean_markdown(feedback.strip())
    return cleaned_feedback
