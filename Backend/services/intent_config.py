"""
Centralized intent configuration for Luna.

This module provides a single place to define all intents and their workflow
configurations. This simplifies adding new intents and ensures consistency
across the system.
"""

from typing import Dict, List, Optional

from pydantic import BaseModel

from services.workflows.ids import Steps
from utils.models import IntentType


class IntentConfig(BaseModel):
    """Configuration for a single intent with workflow support."""

    intent_id: str
    description: str
    workflow_steps: List[str]
    initial_step: str


class IntentRegistry:
    """Central registry for all intent configurations."""

    def __init__(self):
        self._intents: Dict[str, IntentConfig] = {}
        self._initialize_default_intents()

    def _initialize_default_intents(self):
        """Initialize all default intent configurations."""

        # Core workflow intents
        self.register_intent(
            IntentConfig(
                intent_id=IntentType.GENERATE_KUNDLI.value,
                description="Includes profile selection, profile addition, and kundli generation.",
                workflow_steps=[
                    Steps.PROFILE_RESOLUTION.value,
                    Steps.PROFILE_ADDITION.value,
                    Steps.KUNDLI_GENERATION.value,
                ],
                initial_step=Steps.PROFILE_RESOLUTION.value,
            )
        )

        # Profile Q&A workflow
        self.register_intent(
            IntentConfig(
                intent_id=IntentType.PROFILE_QNA.value,
                description="Multi-turn Q&A session based on a specific user profile for personalized astrology insights.",
                workflow_steps=[
                    Steps.PROFILE_RESOLUTION.value,
                    Steps.PROFILE_QNA_STEP.value,
                ],
                initial_step=Steps.PROFILE_RESOLUTION.value,
            )
        )

        # Main menu slash command handler
        self.register_intent(
            IntentConfig(
                intent_id=IntentType.MAIN_MENU.value,
                description="Main menu that can be invoked at any time with slash commands like /luna, /menu, or /help.",
                workflow_steps=[
                    Steps.MAIN_MENU_STEP.value,
                ],
                initial_step=Steps.MAIN_MENU_STEP.value,
            )
        )

        # Fallback intent for unknown/unclassifiable messages
        self.register_intent(
            IntentConfig(
                intent_id=IntentType.UNKNOWN.value,
                description="Fallback for unclear or unclassifiable messages.",
                workflow_steps=[Steps.UNKNOWN_FALLBACK.value],
                initial_step=Steps.UNKNOWN_FALLBACK.value,
            )
        )

        # Additional intents can be added here following the same pattern
        # Example - to add later when workflow steps are implemented:
        #
        # self.register_intent(
        #     IntentConfig(
        #         intent_id="query_kundli",
        #         description="User asks questions about their existing kundli or birthchart.",
        #         workflow_steps=["query_kundli_native"],
        #         initial_step="query_kundli_native",
        #     )
        # )
        #
        # self.register_intent(
        #     IntentConfig(
        #         intent_id="subscribe_predictions",
        #         description="User wants to subscribe to daily, weekly, or monthly predictions.",
        #         workflow_steps=["subscribe_predictions_native"],
        #         initial_step="subscribe_predictions_native",
        #     )
        # )

    def register_intent(self, config: IntentConfig) -> None:
        """Register an intent configuration."""
        self._intents[config.intent_id] = config

    def get_intent_config(self, intent_id: str) -> Optional[IntentConfig]:
        """Get intent configuration by ID."""
        return self._intents.get(intent_id)

    def get_all_intents(self) -> List[str]:
        """Get list of all intent IDs."""
        return list(self._intents.keys())

    def get_intent_descriptions(self) -> Dict[str, str]:
        """Get mapping of intent IDs to descriptions."""
        return {
            intent_id: config.description for intent_id, config in self._intents.items()
        }


# Global intent registry instance
_intent_registry = IntentRegistry()


def get_intent_registry() -> IntentRegistry:
    """Get the global intent registry instance."""
    return _intent_registry


# Convenience functions
def get_all_intents() -> List[str]:
    """Get list of all intent IDs."""
    return _intent_registry.get_all_intents()


def get_intent_descriptions() -> Dict[str, str]:
    """Get mapping of intent IDs to descriptions."""
    return _intent_registry.get_intent_descriptions()


def get_intent_description(intent: str) -> str:
    """Get description for a specific intent."""
    descriptions = get_intent_descriptions()
    return descriptions.get(intent, "")
