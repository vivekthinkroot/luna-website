import logging
from datetime import datetime, timezone
from typing import Any, Dict, List

import pytest

from services.channels import ChannelsService
from utils.models import CanonicalRequestMessage, CanonicalResponseMessage, ContentType
 

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

KUNDLI_TEST_SCENARIOS: List[Dict[str, Any]] = [
    {
        "description": "Add profile multi-turn from scratch",
        "turns": [
            {
                "user_message": "Add a new profile",
                "validate": lambda c: "name" in c.lower() or "who" in c.lower(),
            },
            {
                "user_message": "For myself, name is Test User",
                "validate": lambda c: "birth" in c.lower() or "dob" in c.lower(),
            },
            {
                "user_message": "Born on 1990-01-01 in Test City, male",
                "validate": lambda c: "complete" in c.lower() or "added" in c.lower(),
            },
        ],
        "expected_final": lambda resp: "profile added" in resp.lower(),
    },
    {
        "description": "Generate kundli with existing profile",
        "turns": [
            {
                "user_message": "Generate my kundli",
                "validate": lambda c: "kundli" in c.lower()
                and "generated" in c.lower(),
            },
        ],
        "expected_final": lambda resp: "ascendant" in resp.lower()
        or "summary" in resp.lower(),
    },
    {
        "description": "Generate kundli without profile - remap and chain",
        "setup": "no_profile",  # Assume we clear profile in test
        "turns": [
            {
                "user_message": "Generate my kundli",
                "validate": lambda c: "birth details" in c.lower(),
            },
            {
                "user_message": "Name: Test, DOB: 1990-01-01, Place: Test City, Gender: Male, Relationship: Self",
                "validate": lambda c: "profile added" in c.lower()
                and "kundli generated" in c.lower(),
            },
        ],
        "expected_final": lambda resp: "kundli" in resp.lower()
        and "generated" in resp.lower(),
    },
]

pytestmark = pytest.mark.asyncio


@pytest.fixture(scope="function")
async def kundli_test_env(setup_test_environment):
    env = setup_test_environment
    # Additional setup if needed, e.g., clear session state or profile
    yield env


async def run_kundli_test_turn(
    channels_service: ChannelsService,
    telegram_user_id: str,
    user_message: str,
    mock_send_message: Any,
) -> CanonicalResponseMessage:
    request_message = CanonicalRequestMessage(
        user_id=None,
        channel_type="telegram",
        channel_user_id=telegram_user_id,
        content=user_message,
        content_type=ContentType.TEXT,
        metadata={},
        timestamp=datetime.now(timezone.utc),
    )
    await channels_service.process_incoming_message(request_message)
    mock_send_message.assert_called_once()
    response_message = mock_send_message.call_args[0][1]
    mock_send_message.reset_mock()
    return response_message


async def test_kundli_service_scenarios(kundli_test_env: Dict[str, Any]):
    channels_service = ChannelsService()
    telegram_user_id = kundli_test_env["telegram_user_id"]
    mock_send_message = kundli_test_env["mock_send_message"]

    for i, scenario in enumerate(KUNDLI_TEST_SCENARIOS):
        description = scenario["description"]
        turns = scenario["turns"]
        expected_final = scenario["expected_final"]

        logger.info(f"--- Running Kundli Scenario {i+1}: {description} ---")

        # Setup if needed (e.g., clear profile for no_profile scenarios)
        if scenario.get("setup") == "no_profile":
            # Assuming a way to clear session.current_profile_id; might need actual DB manipulation
            pass  # Placeholder: Clear via DAO if needed

        responses = []
        for turn in turns:
            user_message = turn["user_message"]
            validate_fn = turn["validate"]
            logger.info(f"User Message: '{user_message}'")
            response = await run_kundli_test_turn(
                channels_service, telegram_user_id, user_message, mock_send_message
            )
            response_content = response.content
            logger.info(f"Response: '{response_content}'")
            assert validate_fn(
                response_content
            ), f"Validation failed for turn in {description}"
            responses.append(response_content)

        assert expected_final(
            responses[-1]
        ), f"Final validation failed for {description}"
        logger.info(f"--- Scenario {i+1} Passed ---")

    # Note: PDF/HTML generation moved to standalone script under scripts/
