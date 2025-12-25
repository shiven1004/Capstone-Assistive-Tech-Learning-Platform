from causal_model_handler import ModelHandler
from transformers import pipeline
from langchain_huggingface import HuggingFacePipeline
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from typing import Dict
import re
import random
from logger import Logger

logger = Logger(name="Enhanced Generation", log_file_needed=True, log_file='Logs/enhanced_generation.log', level='DEV')

class EmojiEnhancer:
    """Class to add appropriate emojis to educational responses"""
    
    def __init__(self):
        # Emotion-based emojis
        self.emotion_emojis = {
            'joy': ['😊', '😄', '🌟', '✨', '🎉', '🤗'],
            'sadness': ['💙', '🫂', '🌈', '💜', '🤗'],
            'anger': ['🤝', '💙', '🌸', '🧘‍♀️', '💪'],
            'fear': ['🤗', '💪', '🌟', '🦋', '🌱'],
            'surprise': ['😲', '🤩', '✨', '🎯', '🌟'],
            'disgust': ['🤔', '💭', '🌸', '🌿'],
            'neutral': ['😊', '🌟', '💡', '🎯', '✨'],
            'anxiety': ['🌸', '🫂', '💙', '🌱', '🤗'],
            'frustration': ['💪', '🌟', '🤝', '💙', '🧘‍♀️'],
            'excitement': ['🎉', '🌟', '✨', '🚀', '🎯'],
            'confusion': ['💡', '🤔', '🧩', '🌟', '🔍']
        }
        
        # Learning context emojis
        self.learning_emojis = {
            'math': ['🔢', '➕', '➖', '✖️', '➗', '📐', '📏', '🧮'],
            'science': ['🔬', '🧪', '🌡️', '🔭', '🌍', '⚗️', '🧬'],
            'reading': ['📚', '📖', '📝', '✏️', '📄', '📰'],
            'writing': ['✍️', '📝', '✏️', '🖊️', '📄', '📋'],
            'art': ['🎨', '🖌️', '🖍️', '🌈', '🖼️', '🎭'],
            'music': ['🎵', '🎶', '🎹', '🎸', '🥁', '🎤'],
            'history': ['📜', '🏛️', '👑', '⚔️', '🗿', '📚'],
            'geography': ['🌍', '🗺️', '🏔️', '🌊', '🏜️', '🌋'],
            'general': ['📚', '💡', '🌟', '🎯', '✨']
        }
        
        # Educational activities emojis
        self.activity_emojis = {
            'homework': ['📝', '✏️', '📚', '📋', '🎯'],
            'test': ['📝', '✅', '🎯', '💪', '🌟'],
            'project': ['🔨', '🎨', '📊', '🏗️', '💡'],
            'learning': ['🧠', '💡', '📚', '🌱', '🌟'],
            'understanding': ['💡', '🔍', '🧩', '✨'],
            'practicing': ['🎯', '💪', '🏃‍♀️', '🔄']
        }
        
        # Special needs supportive emojis
        self.special_needs_emojis = {
            'dyslexia': ['👀', '🔤', '📖', '🎧', '💡'],
            'adhd': ['⚡', '🏃‍♀️', '🎯', '🔄', '💪'],
            'learning_difficulty': ['🌱', '💪', '🤗', '🌟', '🎯']
        }
        
        # Encouragement emojis
        self.encouragement_emojis = ['🌟', '💪', '🎉', '✨', '👏', '🚀', '🌈', '🦋']
        
        # Celebration emojis
        self.celebration_emojis = ['🎉', '🎊', '👏', '🌟', '✨', '🏆', '🥇', '💫']

    def add_emojis_to_response(self, response: str, emotion_analysis: Dict) -> str:
        """Add appropriate emojis to the response based on emotion and context"""
        try:
            primary_emotion = emotion_analysis.get('primary_emotion', 'neutral')
            educational_context = emotion_analysis.get('educational_context', 'general')
            special_needs = emotion_analysis.get('special_needs_indicators', [])
            
            # Start with the original response
            enhanced_response = response
            
            # Add opening emoji based on emotion
            opening_emoji = self._get_opening_emoji(primary_emotion)
            if opening_emoji and not enhanced_response.strip().startswith(('😊', '😄', '🌟', '✨', '🎉', '🤗', '💙', '🫂', '🌈')):
                enhanced_response = f"{opening_emoji} {enhanced_response}"
            
            # Add context-specific emojis within the text
            enhanced_response = self._inject_contextual_emojis(enhanced_response, educational_context)
            
            # Add special needs supportive emojis
            enhanced_response = self._add_special_needs_emojis(enhanced_response, special_needs)
            
            # Add encouragement emojis for positive reinforcement
            enhanced_response = self._add_encouragement_emojis(enhanced_response, primary_emotion)
            
            # Add learning-specific emojis
            enhanced_response = self._add_learning_emojis(enhanced_response, educational_context)
            
            return enhanced_response
            
        except Exception as e:
            logger.error(f"Error adding emojis: {str(e)}")
            return response  # Return original response if emoji enhancement fails

    def _get_opening_emoji(self, emotion: str) -> str:
        """Get an appropriate opening emoji based on emotion"""
        emotion_emojis = self.emotion_emojis.get(emotion, self.emotion_emojis['neutral'])
        return random.choice(emotion_emojis)

    def _inject_contextual_emojis(self, text: str, context: str) -> str:
        """Inject emojis based on learning context"""
        # Math-related keywords
        if context == 'math' or any(word in text.lower() for word in ['math', 'number', 'calculate', 'equation', 'solve']):
            emoji = random.choice(self.learning_emojis['math'])
            text = re.sub(r'\b(math|mathematics|number|calculate|equation|solve)\b', 
                         lambda m: f"{m.group()} {emoji}", text, count=1, flags=re.IGNORECASE)
        
        # Science-related keywords
        elif context == 'science' or any(word in text.lower() for word in ['science', 'experiment', 'discover', 'explore']):
            emoji = random.choice(self.learning_emojis['science'])
            text = re.sub(r'\b(science|experiment|discover|explore)\b', 
                         lambda m: f"{m.group()} {emoji}", text, count=1, flags=re.IGNORECASE)
        
        # Reading-related keywords
        elif context == 'reading' or any(word in text.lower() for word in ['read', 'book', 'story', 'text']):
            emoji = random.choice(self.learning_emojis['reading'])
            text = re.sub(r'\b(read|reading|book|story|text)\b', 
                         lambda m: f"{m.group()} {emoji}", text, count=1, flags=re.IGNORECASE)
        
        # Writing-related keywords
        elif context == 'writing' or any(word in text.lower() for word in ['write', 'essay', 'paragraph', 'composition']):
            emoji = random.choice(self.learning_emojis['writing'])
            text = re.sub(r'\b(write|writing|essay|paragraph|composition)\b', 
                         lambda m: f"{m.group()} {emoji}", text, count=1, flags=re.IGNORECASE)
        
        return text

    def _add_special_needs_emojis(self, text: str, special_needs: list) -> str:
        """Add supportive emojis for special needs"""
        if 'dyslexia_pattern' in special_needs:
            if any(word in text.lower() for word in ['read', 'font', 'text-to-speech', 'audio']):
                emoji = random.choice(self.special_needs_emojis['dyslexia'])
                text = text.replace('text-to-speech', f'text-to-speech {emoji}', 1)
        
        if 'adhd_pattern' in special_needs:
            if any(word in text.lower() for word in ['focus', 'break', 'movement', 'attention']):
                emoji = random.choice(self.special_needs_emojis['adhd'])
                text = re.sub(r'\b(focus|break|movement|attention)\b', 
                             lambda m: f"{m.group()} {emoji}", text, count=1, flags=re.IGNORECASE)
        
        return text

    def _add_encouragement_emojis(self, text: str, emotion: str) -> str:
        """Add encouragement emojis for motivation"""
        # Add encouragement for negative emotions
        if emotion in ['sadness', 'anger', 'fear', 'frustration', 'anxiety']:
            encouragement_words = ['you can', 'you\'re doing', 'keep going', 'try again', 'don\'t worry']
            for word in encouragement_words:
                if word in text.lower():
                    emoji = random.choice(self.encouragement_emojis)
                    text = text.replace(word, f"{word} {emoji}", 1)
                    break
        
        # Add celebration for positive words
        celebration_words = ['great', 'excellent', 'awesome', 'wonderful', 'fantastic', 'amazing', 'perfect']
        for word in celebration_words:
            if word in text.lower():
                emoji = random.choice(self.celebration_emojis)
                text = re.sub(rf'\b{word}\b', f"{word} {emoji}", text, count=1, flags=re.IGNORECASE)
                break
        
        return text

    def _add_learning_emojis(self, text: str, context: str) -> str:
        """Add learning activity emojis"""
        # Learning activities
        if any(word in text.lower() for word in ['learn', 'study', 'practice', 'understand']):
            emoji = random.choice(self.activity_emojis['learning'])
            text = re.sub(r'\b(learn|learning|study|studying|practice|practicing|understand|understanding)\b', 
                         lambda m: f"{m.group()} {emoji}", text, count=1, flags=re.IGNORECASE)
        
        # Questions and curiosity
        if '?' in text and any(word in text.lower() for word in ['what', 'how', 'why', 'when', 'where']):
            text = text.replace('?', '? 🤔', 1)
        
        # Tips and suggestions
        if any(word in text.lower() for word in ['tip', 'suggestion', 'try', 'idea']):
            text = re.sub(r'\b(tip|suggestion|try|idea)\b', 
                         lambda m: f"💡 {m.group()}", text, count=1, flags=re.IGNORECASE)
        
        return text

class EducationalEmotionalResponseGenerator:
    def __init__(self, model_name="meta-llama/Llama-3.2-1B-Instruct"):
        logger.debug(f"Initializing EducationalEmotionalResponseGenerator with model: {model_name}")
        try:
            self.handler = ModelHandler(model_name, True)
            model, tokenizer = self.handler.load_model()
            
            # Initialize emoji enhancer
            self.emoji_enhancer = EmojiEnhancer()
            
            self.gen_pipe = pipeline(
                task="text-generation",
                model=model,
                tokenizer=tokenizer,
                max_new_tokens=1500,
                min_new_tokens=50,
                temperature=0.3,
                top_p=0.9,
                top_k=50,
                repetition_penalty=1.1,
                do_sample=True,
                return_full_text=False,
                eos_token_id=tokenizer.eos_token_id,
                pad_token_id=tokenizer.pad_token_id or tokenizer.eos_token_id,
            )
            
            self.llm_chain = HuggingFacePipeline(pipeline=self.gen_pipe)
            
            self.templates = {
                'dyslexia_supportive': """You are a patient, understanding AI tutor specializing in helping children with dyslexia. You understand reading challenges and provide supportive assistance.

Student's message: {user_input}
Detected emotion: {emotion_label}
Educational context: {educational_context}

Guidelines:
- Acknowledge their reading/writing challenges with empathy
- Offer alternative learning methods (audio, visual, kinesthetic)
- Use simple, clear language with shorter sentences
- Suggest tools like text-to-speech or special fonts
- Be patient and encouraging about progress
- Break complex information into smaller chunks
- Use warm, supportive language with emotional expressions

Response:""",

                'adhd_supportive': """You are an energetic, understanding AI tutor who helps children with ADHD stay focused and engaged in learning.

Student's message: {user_input}
Detected emotion: {emotion_label}
Educational context: {educational_context}

Guidelines:
- Acknowledge their attention challenges without judgment
- Suggest movement breaks or fidget strategies
- Keep responses concise and well-structured
- Use engaging, interactive language
- Offer multiple short activities instead of long tasks
- Celebrate small wins and progress
- Help them refocus when distracted
- Use enthusiastic and encouraging expressions

Response:""",

                'learning_supportive': """You are a compassionate AI tutor who helps children overcome learning difficulties with patience and creativity.

Student's message: {user_input}
Detected emotion: {emotion_label}
Educational context: {educational_context}

Guidelines:
- Validate their feelings about learning challenges
- Offer alternative explanations and approaches
- Use encouraging, growth-mindset language
- Suggest breaking tasks into smaller steps
- Provide specific, actionable help
- Remind them that everyone learns differently
- Celebrate effort over perfection
- Use warm and supportive expressions

Response:""",

                'confidence_building': """You are an encouraging AI tutor focused on building student confidence and self-esteem.

Student's message: {user_input}
Detected emotion: {emotion_label}
Educational context: {educational_context}

Guidelines:
- Address negative self-talk with gentle correction
- Highlight their strengths and past successes
- Use growth mindset language ("yet", "learning", "growing")
- Provide specific, achievable next steps
- Share that mistakes are part of learning
- Be enthusiastic about their potential
- Ask about their interests to build connections
- Use positive and uplifting expressions

Response:""",

                'standard': """You are a friendly, supportive AI tutor who helps children with their learning in an encouraging way.

Student's message: {user_input}
Detected emotion: {emotion_label}

Guidelines:
- Be warm, patient, and age-appropriate
- Acknowledge their emotions with empathy
- Provide helpful, educational responses
- Encourage curiosity and questions
- Keep responses engaging and conversational
- Celebrate learning moments
- Ask follow-up questions when appropriate
- Use cheerful and supportive expressions

Response:"""
            }
            
            logger.debug("Educational response generation pipeline loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load enhanced generation model: {str(e)}")
            raise

    def generate_educational_response(self, user_input: str, emotion_analysis: Dict) -> str:
        """
        Generate context-aware educational response
        """
        logger.debug(f"Generating educational response for emotion analysis: {emotion_analysis}")
        
        try:
            if not user_input or not user_input.strip():
                return "I'm here to help you learn! What would you like to talk about or work on today?"
            
            recommended_approach = emotion_analysis.get('recommended_approach', 'standard')
            template_key = recommended_approach if recommended_approach in self.templates else 'standard'
            
            logger.debug(f"Using template: {template_key}")
            
            template = self.templates[template_key]
            prompt = PromptTemplate.from_template(template)
            chain = prompt | self.llm_chain | StrOutputParser()
            
            inputs = {
                "user_input": user_input.strip(),
                "emotion_label": emotion_analysis.get('primary_emotion', 'neutral'),
            }
            
            if 'educational_context' in emotion_analysis:
                inputs["educational_context"] = emotion_analysis['educational_context']
            
            logger.debug("Invoking enhanced generation chain")
            result = chain.invoke(inputs)
            
            response = result.strip()
            
            prefixes_to_remove = ["Response:", "Assistant:", "AI:", "Bot:", "Tutor:"]
            for prefix in prefixes_to_remove:
                if response.startswith(prefix):
                    response = response[len(prefix):].strip()
            
            response = self._enhance_response_for_special_needs(
                response, emotion_analysis.get('special_needs_indicators', [])
            )
            
            # Add emojis to the response
            response = self.emoji_enhancer.add_emojis_to_response(response, emotion_analysis)
            
            if len(response) < 15:
                fallback = self._get_educational_fallback(emotion_analysis)
                return self.emoji_enhancer.add_emojis_to_response(fallback, emotion_analysis)
            
            logger.debug(f"Generated educational response: {len(response)} characters")
            return response
            
        except Exception as e:
            logger.error(f"Error generating educational response: {str(e)}")
            fallback = self._get_educational_fallback(emotion_analysis)
            return self.emoji_enhancer.add_emojis_to_response(fallback, emotion_analysis)
    
    def _enhance_response_for_special_needs(self, response: str, indicators: list) -> str:
        """Add special formatting or suggestions based on special needs indicators"""
        if 'dyslexia_pattern' in indicators:
            if len(response) > 100:
                response += "\n\n💡 Tip: Try using text-to-speech or a dyslexia-friendly font if reading this is challenging! 👀"
        
        elif 'adhd_pattern' in indicators:
            response += "\n\n⚡ Remember: It's okay to take a movement break if you need one! 🏃‍♀️"
        
        return response
    
    def _get_educational_fallback(self, emotion_analysis: Dict) -> str:
        """Educational fallback responses"""
        emotion = emotion_analysis.get('primary_emotion', 'neutral')
        context = emotion_analysis.get('educational_context', 'general')
        
        fallbacks = {
            ('sadness', 'frustration_learning'): "Learning can feel hard sometimes, and that's completely normal! Every student faces challenges. What specific part would you like help with? We can break it down together.",
            ('anger', 'frustration_learning'): "I can hear that you're really frustrated with this. That's okay - learning new things can be tough! Let's take a step back and try a different approach. What's the hardest part for you?",
            ('fear', 'anxiety_learning'): "It's natural to feel nervous about learning new things. You're brave for trying! Remember, making mistakes is how we learn. What would help you feel more confident?",
            ('neutral', 'dyslexia_pattern'): "I understand that reading and writing can be challenging. There are many ways to learn, and we'll find what works best for you. What would you like to work on?",
            ('neutral', 'adhd_pattern'): "I know it can be hard to focus sometimes. That's okay! Let's find ways to make learning more engaging and fun for you. What interests you most?",
        }
        
        key = (emotion, context)
        if key in fallbacks:
            return fallbacks[key]
        
        return "I'm here to help you learn and grow! Every question you have is important. What would you like to explore together?"

educational_response_generator = EducationalEmotionalResponseGenerator()

def generate_educational_response(user_input: str, emotion_analysis: Dict) -> str:
    """Global function for educational response generation"""
    return educational_response_generator.generate_educational_response(user_input, emotion_analysis)
