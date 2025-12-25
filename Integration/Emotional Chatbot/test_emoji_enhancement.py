#!/usr/bin/env python3
"""
Test script to demonstrate emoji enhancement in the generation pipeline
"""

from generation_pipeline import EmojiEnhancer

def test_emoji_enhancement():
    """Test the emoji enhancement functionality"""
    
    # Initialize the emoji enhancer
    emoji_enhancer = EmojiEnhancer()
    
    # Test cases with different emotions and contexts
    test_cases = [
        {
            'response': "Great job on solving that math problem! You're really understanding equations well.",
            'emotion_analysis': {
                'primary_emotion': 'joy',
                'educational_context': 'math',
                'special_needs_indicators': []
            }
        },
        {
            'response': "I know reading can be challenging sometimes. Let's try using text-to-speech to help you understand the story better.",
            'emotion_analysis': {
                'primary_emotion': 'sadness',
                'educational_context': 'reading',
                'special_needs_indicators': ['dyslexia_pattern']
            }
        },
        {
            'response': "It's okay to feel frustrated with this science experiment. Let's take a break and try a different approach.",
            'emotion_analysis': {
                'primary_emotion': 'anger',
                'educational_context': 'science',
                'special_needs_indicators': ['adhd_pattern']
            }
        },
        {
            'response': "You're doing amazing work on your writing assignment! Every paragraph you write shows improvement.",
            'emotion_analysis': {
                'primary_emotion': 'excitement',
                'educational_context': 'writing',
                'special_needs_indicators': []
            }
        },
        {
            'response': "What's your favorite subject to learn about? I'm here to help you explore any topic you find interesting.",
            'emotion_analysis': {
                'primary_emotion': 'neutral',
                'educational_context': 'general',
                'special_needs_indicators': []
            }
        }
    ]
    
    print("🎯 Testing Emoji Enhancement System\n")
    print("=" * 60)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📝 Test Case {i}:")
        print(f"Original: {test_case['response']}")
        print(f"Emotion: {test_case['emotion_analysis']['primary_emotion']}")
        print(f"Context: {test_case['emotion_analysis']['educational_context']}")
        
        enhanced_response = emoji_enhancer.add_emojis_to_response(
            test_case['response'], 
            test_case['emotion_analysis']
        )
        
        print(f"Enhanced: {enhanced_response}")
        print("-" * 60)
    
    print("\n✨ Emoji enhancement testing completed!")

if __name__ == "__main__":
    test_emoji_enhancement()
