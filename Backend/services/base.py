"""
Base definitions for Luna's router and domain services.
This file provides the domain service interface using the centralized
intent configuration system for workflow-based intent handling.
"""

from abc import ABC, abstractmethod

from utils.models import CanonicalRequestMessage, CanonicalResponseMessage, IntentType
from utils.sessions import Session

# Import centralized intent configuration
from .intent_config import (
    get_all_intents,
    get_intent_description,
    get_intent_descriptions,
)

# Re-export for compatibility
INTENT_DESCRIPTIONS = get_intent_descriptions()


class DomainService(ABC):
    """
    Abstract base class for all domain services.

    Domain services handle specific intents and provide the business logic
    for processing user requests. Each service should implement the process
    method to handle requests related to its domain.
    """

    @abstractmethod
    async def process(
        self, message: CanonicalRequestMessage, session: Session, predicted_intent: str
    ) -> CanonicalResponseMessage:
        """
        Process a user message based on the predicted intent.

        Args:
            message (CanonicalRequestMessage): The user message with metadata
            session (Session): The user's session data
            predicted_intent (str): The intent predicted by the router

        Returns:
            CanonicalResponseMessage: Response containing text, artifacts, and other metadata
        """
        pass
