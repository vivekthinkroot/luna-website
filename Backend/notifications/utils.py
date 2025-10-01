"""
Utility functions for notification message generation.
"""

import random
from typing import Optional


def generate_mock_message(message_type: str, user_name: Optional[str] = None) -> str:
    """
    Generate simple, direct messages for notifications.
    
    Args:
        message_type (str): Type of message to generate
        user_name (Optional[str]): User's name for personalization (not used)
        
    Returns:
        str: Generated message
    """
    if message_type == "horoscope":
        messages = [
            "🌟 Here is your daily horoscope prediction.",
            "✨ Your daily horoscope is ready.",
            "🔮 Check out your daily horoscope.",
            "⭐ Your horoscope for today.",
            "🌙 Here's your daily horoscope reading."
        ]
    elif message_type == "tarot":
        messages = [
            "🎴 Here is your daily tarot reading.",
            "🃏 Your tarot cards are ready.",
            "✨ Check out your daily tarot prediction.",
            "🌟 Your tarot reading for today.",
            "🔮 Here's your daily tarot guidance."
        ]
    elif message_type == "numerology":
        messages = [
            "🔢 Here is your daily numerology reading.",
            "📊 Your numerology prediction is ready.",
            "✨ Check out your daily numerology.",
            "🌟 Your numerology for today.",
            "🔮 Here's your daily numerology guidance."
        ]
    else:  # general
        messages = [
            "🌟 Here is your daily prediction.",
            "✨ Your daily reading is ready.",
            "🔮 Check out your daily forecast.",
            "⭐ Your prediction for today.",
            "🌙 Here's your daily guidance."
        ]
    
    return random.choice(messages)


def generate_custom_message(user_name: Optional[str] = None) -> str:
    """
    Generate a simple custom message.
    
    Args:
        user_name (Optional[str]): User's name for personalization (not used)
        
    Returns:
        str: Custom message
    """
    custom_messages = [
        "💫 Here is your personalized prediction.",
        "🌟 Your custom reading is ready.",
        "✨ Check out your personalized forecast.",
        "🔮 Your custom prediction for today.",
        "🌙 Here's your personalized guidance."
    ]
    
    return random.choice(custom_messages)
