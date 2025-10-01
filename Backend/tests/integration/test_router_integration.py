import logging
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List

import pytest

from services.channels import ChannelsService
from utils.models import CanonicalRequestMessage, CanonicalResponseMessage, ContentType

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Test Scenarios Configuration ---

TEST_SCENARIOS: List[Dict[str, Any]] = [
    {
        "description": "Initial user message to generate a kundli",
        "user_message": "Can you generate my kundli for me please?",
        "expected_intent": "generate_kundli",
        "validate_response": lambda content: "need your birth details"
        in content.lower(),
    },
    {
        "description": "Follow-up question about career, relying on context",
        "user_message": "What about my career?",
        "expected_intent": "query_kundli",
        "validate_response": lambda content: "based on your kundli" in content.lower(),
    },
    {
        "description": "User asks an astrology-related question.",
        "user_message": "What does it mean if my moon is in Scorpio?",
        "expected_intent": "general_qna",
        "validate_response": lambda content: "scorpio" in content.lower()
        and "moon" in content.lower(),
    },
    {
        "description": "User subscribes to daily predictions.",
        "user_message": "Sign me up for daily predictions.",
        "expected_intent": "subscribe_predictions",
        "validate_response": lambda content: "subscribed" in content.lower()
        and "daily" in content.lower(),
    },
    {
        "description": "User unsubscribes from all notifications.",
        "user_message": "I want to stop all notifications.",
        "expected_intent": "unsubscribe_predictions",
        "validate_response": lambda content: "unsubscribed" in content.lower()
        or "notifications turned off" in content.lower(),
    },
    {
        "description": "User adds a new profile (e.g., for family or friend).",
        "user_message": "Add a profile for my daughter Priya.",
        "expected_intent": "add_profile",
        "validate_response": lambda content: "profile added" in content.lower()
        or "added" in content.lower(),
    },
    {
        "description": "User switches to a different profile.",
        "user_message": "Switch to Priya's profile.",
        "expected_intent": "switch_profile",
        "validate_response": lambda content: "switched" in content.lower()
        or "now using" in content.lower(),
    },
    {
        "description": "User greets the bot.",
        "user_message": "Hello there!",
        "expected_intent": "help",
        "validate_response": lambda content: "hello" in content.lower()
        or "hi" in content.lower()
        or "help" in content.lower(),
    },
    {
        "description": "User asks for help.",
        "user_message": "What can you do?",
        "expected_intent": "help",
        "validate_response": lambda content: "i can" in content.lower()
        or "help" in content.lower(),
    },
    {
        "description": "User sends a voice message (simulated as text for test).",
        "user_message": "[voice message: What is my horoscope for today?]",
        "expected_intent": "general_qna",
        "validate_response": lambda content: "horoscope" in content.lower()
        and "today" in content.lower(),
    },
    {
        "description": "User sends an unsupported or unclear message.",
        "user_message": "Blah blah blah",
        "expected_intent": "unknown",
        "validate_response": lambda content: "didn't understand" in content.lower()
        or "can you rephrase" in content.lower(),
    },
]

# Mark the entire module to use pytest-asyncio
pytestmark = pytest.mark.asyncio


async def run_test_step(
    channels_service: ChannelsService,
    telegram_user_id: str,
    user_message: str,
    mock_send_message: Any,
) -> CanonicalResponseMessage:
    """Helper function to process a single test step."""
    request_message = CanonicalRequestMessage(
        user_id=None,  # Resolved by ChannelsService
        channel_type="telegram",
        channel_user_id=telegram_user_id,
        content=user_message,
        content_type=ContentType.TEXT,
        metadata={},
        timestamp=datetime.now(timezone.utc),
    )

    await channels_service.process_incoming_message(request_message)

    # Ensure the mocked send_message was called
    mock_send_message.assert_called_once()
    # The send_message mock is called with (channel_user_id, response_message)
    # We need to grab the second argument, which is the message object.
    response_message = mock_send_message.call_args[0][1]
    mock_send_message.reset_mock()

    return response_message


async def test_intent_classification_scenarios(setup_test_environment: Dict[str, Any]):
    """
    Runs a series of JSON-driven conversational scenarios to test intent classification.

    This test iterates through a predefined list of scenarios, simulating a user
    conversation turn by turn. It verifies that the router correctly classifies
    the intent at each step and that the service response is appropriate.

    Args:
        setup_test_environment: The pytest fixture that provides test user details
                                and the mocked send function.
    """
    channels_service = ChannelsService()
    telegram_user_id = setup_test_environment["telegram_user_id"]
    mock_send_message = setup_test_environment["mock_send_message"]

    for i, scenario in enumerate(TEST_SCENARIOS):
        description = scenario["description"]
        user_message = scenario["user_message"]
        expected_intent = scenario["expected_intent"]
        validate_fn: Callable[[str], bool] = scenario["validate_response"]

        logger.info(f"--- Running Scenario {i+1}: {description} ---")
        logger.info(f"User Message: '{user_message}'")

        response = await run_test_step(
            channels_service, telegram_user_id, user_message, mock_send_message
        )

        # 1. Validate the predicted intent
        predicted_intent = response.metadata.get("predicted_intent")
        logger.info(f"Predicted Intent: '{predicted_intent}'")
        assert (
            predicted_intent == expected_intent
        ), f"Failed: Expected intent '{expected_intent}', but got '{predicted_intent}'"

        # 2. Validate the response content
        response_content = response.content
        logger.info(f"Response Content: '{response_content}'")
        assert validate_fn(
            response_content
        ), f"Failed: Response content validation failed for intent '{expected_intent}'"

        logger.info(f"--- Scenario {i+1} Passed ---")
