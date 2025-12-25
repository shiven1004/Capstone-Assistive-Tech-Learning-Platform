# enhanced_main.py
from emotion_detection_pipeline import detect_enhanced_emotion
from generation_pipeline import generate_educational_response
from logger import Logger
import sys
from typing import Dict
from datetime import datetime
from conversation_vectorstore import log_conversation_to_store

logger = Logger(name="Educational ChatBot", log_file_needed=True, log_file='Logs/educational_chatbot.log', level='DEV')

class EducationalChatbot:
    def __init__(self):
        self.conversation_history = []
        self.current_conversation_messages = []  # Track messages for vectorstore
        self.user_id = None  # Will be set at start of chat
        self.student_profile = {
            'session_count': 0,
            'identified_needs': set(),
            'learning_preferences': {},
            'emotional_patterns': []
        }
    
    def display_welcome(self):
        """Display educational welcome message"""
        logger.debug("Displaying educational welcome message")
        print("🎓 Educational Support Chatbot v3.0")
        print("=" * 50)
        print("Hello! I'm your AI learning companion. I'm here to help you with:")
        print("• Homework and study questions")
        print("• Learning difficulties and challenges")
        print("• Building confidence in your abilities")
        print("• Finding new ways to understand topics")
        print("• Providing emotional support during learning")
        print("\nI understand that everyone learns differently, and I'm here to support you!")
        print("=" * 50)
        print("\nCommands: 'exit', 'quit', 'help', or 'profile' to see your learning profile")
        print()

    def display_help(self):
        """Display educational help"""
        logger.debug("User requested educational help information")
        print("\n📚 How I can help you:")
        print("• Ask me about any subject or homework problem")
        print("• Tell me about learning challenges you're facing")
        print("• Share how you're feeling about school or studying")
        print("• Ask for study tips and learning strategies")
        print("• Get encouragement when you're struggling")
        print("\n💡 Tips for better conversations:")
        print("• Be specific about what you're working on")
        print("• Let me know if you have dyslexia, ADHD, or other learning differences")
        print("• Tell me what's confusing or frustrating you")
        print("• Ask questions - there's no such thing as a silly question!")
        print("\nCommands: 'exit' to leave, 'help' for this message, 'profile' to see your learning profile")
        print()

    def display_profile(self):
        """Show student's learning profile"""
        print(f"\n👤 Your Learning Profile:")
        print(f"Sessions completed: {self.student_profile['session_count']}")
        
        if self.student_profile['identified_needs']:
            print(f"Learning patterns I've noticed: {', '.join(self.student_profile['identified_needs'])}")
        
        if self.student_profile['emotional_patterns']:
            recent_emotions = self.student_profile['emotional_patterns'][-5:]
            print(f"Recent emotional patterns: {', '.join(recent_emotions)}")
        
        print()

    def update_student_profile(self, emotion_analysis: Dict, user_input: str):
        """Update student profile based on conversation"""
        # Track emotional patterns
        emotion = emotion_analysis.get('primary_emotion', 'neutral')
        self.student_profile['emotional_patterns'].append(emotion)
        
        # Keep only recent patterns
        if len(self.student_profile['emotional_patterns']) > 20:
            self.student_profile['emotional_patterns'] = self.student_profile['emotional_patterns'][-20:]
        
        # Identify learning needs
        special_needs = emotion_analysis.get('special_needs_indicators', [])
        for need in special_needs:
            self.student_profile['identified_needs'].add(need)
        
        educational_context = emotion_analysis.get('educational_context', '')
        if educational_context and educational_context != 'general':
            self.student_profile['identified_needs'].add(educational_context)

    def chat_loop(self):
        """Enhanced educational chat loop"""
        logger.debug("Starting educational chat application")
        
        # Get user ID at start of session
        print("\n👋 Welcome to the Educational Support Chatbot!")
        self.user_id = input("Please enter your name or user ID: ").strip() or "anonymous"
        logger.debug(f"Session started for user: {self.user_id}")
        
        self.display_welcome()
        
        try:
            while True:
                try:
                    # Get user input
                    user_input = input("You: ").strip()
                    logger.debug(f"User input: '{user_input[:50]}...'")
                    
                    # Handle commands
                    if user_input.lower() in ("exit", "quit", "bye", "goodbye"):
                        logger.debug("User ending session")
                        print(f"\n🌟 Great chatting with you! You completed {self.student_profile['session_count']} learning conversations.")
                        print("Keep being curious and remember - every question helps you grow! 📚")
                        
                        # Save conversation to vectorstore before exiting
                        if self.current_conversation_messages:
                            conversation = {
                                'messages': self.current_conversation_messages,
                                'timestamp': datetime.now().isoformat()
                            }
                            log_conversation_to_store(conversation, 'emotional', self.user_id)
                            logger.debug(f"Saved {len(self.current_conversation_messages)} messages to vectorstore for {self.user_id}")
                        
                        break
                    
                    elif user_input.lower() == "help":
                        self.display_help()
                        continue
                    
                    elif user_input.lower() == "profile":
                        self.display_profile()
                        continue
                    
                    elif not user_input:
                        print("Feel free to ask me anything about learning, homework, or how you're feeling about school!\n")
                        continue
                    
                    self.student_profile['session_count'] += 1
                    
                    # Enhanced emotion detection
                    try:
                        emotion_analysis = detect_enhanced_emotion(user_input, {
                            'conversation_history': self.conversation_history[-3:],
                            'student_profile': self.student_profile
                        })
                        
                        # Display emotion with educational context
                        emotion_display = f"{emotion_analysis['primary_emotion'].title()}"
                        if emotion_analysis['educational_context'] != 'general':
                            emotion_display += f" (Learning context: {emotion_analysis['educational_context']})"
                        
                        confidence = emotion_analysis.get('confidence', 0.0)
                        print(f"[Detected: {emotion_display} - {confidence:.1%} confidence]")
                        
                        # Show special needs indicators if detected
                        if emotion_analysis.get('special_needs_indicators'):
                            indicators_text = ', '.join(emotion_analysis['special_needs_indicators']).replace('_', ' ')
                            print(f"[Learning pattern noted: {indicators_text}]")
                        
                        logger.debug(f"Enhanced emotion analysis: {emotion_analysis}")
                        
                    except Exception as e:
                        logger.error(f"Enhanced emotion detection failed: {str(e)}")
                        emotion_analysis = {
                            'primary_emotion': 'neutral',
                            'confidence': 0.5,
                            'educational_context': 'general',
                            'special_needs_indicators': [],
                            'recommended_approach': 'standard'
                        }
                        print("[Using standard response mode]")
                    
                    # Generate educational response
                    try:
                        response = generate_educational_response(user_input, emotion_analysis)
                        print(f"AI Tutor: {response}\n")
                        
                        # Update student profile
                        self.update_student_profile(emotion_analysis, user_input)
                        
                        # Add to conversation history and vectorstore tracking
                        self.conversation_history.append({
                            'user_input': user_input,
                            'emotion_analysis': emotion_analysis,
                            'response': response
                        })
                        
                        # Track messages for vectorstore
                        self.current_conversation_messages.append({
                            'role': 'user',
                            'content': user_input
                        })
                        self.current_conversation_messages.append({
                            'role': 'assistant',
                            'content': response
                        })
                        
                        # Keep history manageable
                        if len(self.conversation_history) > 10:
                            self.conversation_history = self.conversation_history[-10:]
                        
                        logger.debug("Educational response generated successfully")
                        
                    except Exception as e:
                        logger.error(f"Educational response generation failed: {str(e)}")
                        fallback = "I'm having trouble generating a response right now. Could you try rephrasing your question or telling me more about what you're working on?"
                        print(f"AI Tutor: {fallback}\n")
                    
                except KeyboardInterrupt:
                    logger.debug("Chat interrupted by user")
                    print("\n\nConversation paused. Thanks for learning with me! 📖")
                    
                    # Save conversation to vectorstore before exiting
                    if self.current_conversation_messages:
                        conversation = {
                            'messages': self.current_conversation_messages,
                            'timestamp': datetime.now().isoformat()
                        }
                        log_conversation_to_store(conversation, 'emotional', self.user_id)
                        logger.debug(f"Saved {len(self.current_conversation_messages)} messages to vectorstore")
                    
                    break
                except EOFError:
                    logger.debug("Chat ended due to EOF")
                    print("\n\nSee you next time! Keep being awesome at learning! 🌟")
                    
                    # Save conversation to vectorstore before exiting
                    if self.current_conversation_messages:
                        conversation = {
                            'messages': self.current_conversation_messages,
                            'timestamp': datetime.now().isoformat()
                        }
                        log_conversation_to_store(conversation, 'emotional', self.user_id)
                        logger.debug(f"Saved {len(self.current_conversation_messages)} messages to vectorstore")
                    
                    break
                except Exception as e:
                    logger.error(f"Error in chat loop: {str(e)}")
                    print("Something went wrong, but let's keep learning together! Try again.\n")
        
        except Exception as e:
            logger.critical(f"Critical error in educational chat: {str(e)}")
            print("Critical error occurred. Please restart the application.")
            sys.exit(1)

if __name__ == "__main__":
    logger.debug("Starting Educational Chatbot application")
    try:
        chatbot = EducationalChatbot()
        chatbot.chat_loop()
    except Exception as e:
        logger.critical(f"Application failed to start: {str(e)}")
        sys.exit(1)
    finally:
        logger.debug("Educational application shutdown complete")
