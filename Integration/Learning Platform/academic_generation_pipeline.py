import json
import os
from model_handler import ModelHandler
from transformers import pipeline
from langchain_huggingface import HuggingFacePipeline
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from logger import Logger

# Initialize logger for pipeline
log_dir = os.path.join(os.path.dirname(__file__), "Logs")
os.makedirs(log_dir, exist_ok=True)
pipeline_logger = Logger(
    name="AcademicPipeline",
    log_file_needed=True,
    log_file=os.path.join(log_dir, "pipeline.log"),
    level="DEV"
)

pipeline_logger.info("Initializing academic generation pipeline...")

# Load model once, with correct argument order: model_name, quantize, model_path
try:
    pipeline_logger.info("Loading language model: meta-llama/Llama-3.2-1B-Instruct")
    model = ModelHandler(
        model_name="meta-llama/Llama-3.2-1B-Instruct",
        quantize=False
    )
    loaded_model, corresponding_tokenizer = model.load_model()
    pipeline_logger.info("Model loaded successfully")
except Exception as e:
    pipeline_logger.error(f"Failed to load model: {str(e)}")
    raise

def get_academic_prompt_template():
    """Return academic tutor prompt template."""
    return """Answer this question directly and clearly: {specification}

Provide a helpful explanation using:
- Simple, everyday words
- Short, clear sentences
- Concrete examples if needed
- Step-by-step breakdown for complex topics

Give ONLY your direct answer. Do NOT write dialogue, conversations, or ask follow-up questions.

Answer:"""

def gen_chain():
    """Create the generation pipeline (text-generation → parser)."""
    try:
        pipeline_logger.debug("Initializing text generation pipeline")
        pipe = pipeline(
            "text-generation",
            model=loaded_model,
            tokenizer=corresponding_tokenizer,
            max_new_tokens=2048,
            do_sample=True,
            temperature=0.3,
            eos_token_id=corresponding_tokenizer.eos_token_id,
            pad_token_id=corresponding_tokenizer.eos_token_id,
            return_full_text=False,
        )
        pipeline_logger.info("Text generation pipeline initialized successfully")
        return HuggingFacePipeline(pipeline=pipe) | StrOutputParser()
    except Exception as e:
        pipeline_logger.error(f"Failed to initialize text generation pipeline: {str(e)}")
        raise

# Initialize chain
chain = gen_chain()

def get_model_handler():
    """Return a handler object with generate method for compatibility."""
    class Handler:
        def generate(self, prompt, max_new_tokens=256, temperature=0.3, return_json=False):
            try:
                result = chain.invoke(prompt)
                return result
            except Exception:
                return ""
    return Handler()

def get_chat_response(query: str, chat_history=None) -> str:
    """Get chat response for academic questions."""
    try:
        pipeline_logger.info(f"Processing chat query: {query[:100]}")
        
        if chat_history and len(chat_history) > 0:
            context = ""
            for msg in chat_history[-6:]:
                role = "Student" if msg['role'] == 'user' else "Tutor"
                context += f"{role}: {msg['content']}\n"
            
            prompt_text = f"""Continue this conversation by answering the student's question directly.

Previous conversation:
{context}

Student: {query}

Provide a clear, direct answer using simple words and short sentences. Do NOT write dialogue, role-play, or ask questions back. Just answer helpfully.

Answer:"""
        else:
            prompt_text = get_academic_prompt_template().replace("{specification}", query)
        
        template = PromptTemplate.from_template(template="{specification}")
        specific_chain = template | chain
        result = specific_chain.invoke({"specification": prompt_text})
        cleaned = _clean_output(result)
        
        if cleaned:
            pipeline_logger.info(f"Chat response generated successfully: {cleaned[:100]}")
            return cleaned
        else:
            pipeline_logger.warning("Empty response generated after cleaning")
            return "I apologize, but I couldn't generate a response."
    except Exception as e:
        pipeline_logger.error(f"Error generating chat response: {str(e)}")
        return f"Error: {str(e)}"

def _clean_output(text: str) -> str:
    """Clean output by removing role labels and duplicate sentences."""
    if not text:
        return ""
    s = text.strip()
    s = s.replace("Tutor:", "").replace("Student:", "").replace("Assistant:", "")
    
    import re
    parts = re.split(r"(?<=[.!?])\s+", s)
    out = []
    seen = set()
    for p in parts:
        q = p.strip()
        if not q:
            continue
        key = q.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(q)
    
    return " ".join(out).strip()
