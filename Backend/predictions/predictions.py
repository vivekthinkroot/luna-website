"""
Predictions service for Luna.
Handles daily, weekly, and monthly predictions based on user profiles.
"""

from services.base import DomainService
from utils.logger import get_logger
from utils.models import CanonicalRequestMessage, CanonicalResponseMessage
from utils.sessions import Session

logger = get_logger()


class PredictionsService(DomainService):
    """
    Service for handling prediction-related intents.
    Implements the DomainService interface.
    """

    async def process(
        self, message: CanonicalRequestMessage, session: Session, predicted_intent: str
    ) -> CanonicalResponseMessage:
        """
        Process prediction-related intents.

        Args:
            message (CanonicalRequestMessage): The user message
            session (Session): User session data
            predicted_intent (str): The predicted intent from the router

        Returns:
            Dict[str, Any]: Response with text and optional artifacts
        """
        # Handle different intents
        if predicted_intent == "subscribe_predictions":
            return await self._handle_subscribe_predictions(message, session)
        elif predicted_intent == "unsubscribe_predictions":
            return await self._handle_unsubscribe_predictions(message, session)
        else:
            return message.create_text_response(
                content="I'm not sure how to help with that prediction request. Would you like to subscribe to daily predictions or ask about your horoscope?",
            )

    async def _handle_subscribe_predictions(
        self, message: CanonicalRequestMessage, session: Session
    ) -> CanonicalResponseMessage:
        """Handle subscription to predictions."""
        # Check if user has a profile
        profile_id = session.current_profile_id

        if not profile_id:
            return message.create_text_response(
                content="I don't see any profile associated with your account. Would you like to create one first so I can provide personalized predictions?",
                metadata={"continue_multi_turn": True},
            )

        # Extract the prediction frequency from the message
        # In a real implementation, this would use NLP to understand the request
        message_text = getattr(message, "content", "").lower()

        frequency = "daily"  # Default
        if "weekly" in message_text:
            frequency = "weekly"
        elif "monthly" in message_text:
            frequency = "monthly"

        # In a real implementation, this would update the database
        return message.create_text_response(
            content=f"Great! You're now subscribed to {frequency} predictions. I'll send them to you at the start of each {frequency[:-2] if frequency != 'daily' else 'day'}. Here's your first prediction:\n\n"
            + self._get_sample_prediction(frequency),
        )

    async def _handle_unsubscribe_predictions(
        self, message: CanonicalRequestMessage, session: Session
    ) -> CanonicalResponseMessage:
        """Handle unsubscription from predictions."""
        # In a real implementation, this would update the database
        return message.create_text_response(
            content="You've been unsubscribed from predictions. You can subscribe again anytime by asking for daily, weekly, or monthly predictions.",
        )

    def _get_sample_prediction(self, frequency: str) -> str:
        """Get a sample prediction based on frequency."""
        if frequency == "daily":
            return "Today is a favorable day for communication and short trips. Your ruling planet Mercury forms a harmonious aspect with Jupiter, bringing opportunities for learning and sharing ideas. Focus on expressing yourself clearly in professional settings."
        elif frequency == "weekly":
            return "This week brings a focus on relationships and partnerships. The full moon in your opposite sign highlights the need for balance between personal needs and the needs of others. Wednesday and Thursday are particularly favorable for important conversations and negotiations."
        else:  # monthly
            return "This month emphasizes career growth and public recognition. The solar eclipse in your 10th house on the 15th may bring unexpected opportunities for advancement. Be prepared to step into leadership roles and showcase your talents. The last week of the month is ideal for networking and forming strategic alliances."


# Create a singleton instance
predictions_service = PredictionsService()


# Function to expose the service's process method directly
async def process(
    message: CanonicalRequestMessage, session: Session, predicted_intent: str
) -> CanonicalResponseMessage:
    """
    Process function that delegates to the PredictionsService instance.
    Maintains backward compatibility with the router's expected interface.
    """
    return await predictions_service.process(message, session, predicted_intent)
