import asyncio
import logging
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy.exc import NoResultFound

from dao.profiles import ProfileDAO
from dao.users import UserDAO
from data.models import ChannelType, Gender, RelationshipType

# Configure logging for tests
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Test User Configuration ---
TEST_USER_PHONE = "+9999999999"
TEST_USER_EMAIL = "test.user@lunatester.com"
TEST_TELEGRAM_ID = "tele-test-12345"
TEST_PROFILE_NAME = "Test User Profile"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def setup_test_environment(event_loop):
    """
    Prepares the test environment for integration tests.

    This session-scoped fixture ensures that a test user, profile, and channel
    link exist in the database, creating them if necessary. It also mocks the
    outbound Telegram sender to prevent real messages from being sent.

    This approach ensures test isolation and consistency without needing to
    re-create the user for every test run.
    """
    logger.info("--- Setting up test environment ---")

    user_dao = UserDAO()
    profile_dao = ProfileDAO()

    # 1. Get or Create Test User
    try:
        user = user_dao.get_user_by_phone(TEST_USER_PHONE)
        if not user:
            raise NoResultFound()
        logger.info(f"Found existing test user: {user.user_id}")
    except NoResultFound:
        logger.info(f"Creating new test user with phone: {TEST_USER_PHONE}")
        user = user_dao.create_user(phone=TEST_USER_PHONE, email=TEST_USER_EMAIL)

    # 2. Get or Create Telegram Channel Link
    try:
        channel_user = user_dao.get_user_by_channel(
            ChannelType.TELEGRAM, TEST_TELEGRAM_ID
        )
        if not channel_user or channel_user.user_id != user.user_id:
            raise NoResultFound()
        logger.info(f"Found existing channel link for user {user.user_id}")
    except NoResultFound:
        logger.info(f"Linking user {user.user_id} to Telegram ID {TEST_TELEGRAM_ID}")
        user_dao.link_channel(
            user_id=str(user.user_id),
            channel_type=ChannelType.TELEGRAM,
            user_identity=TEST_TELEGRAM_ID,
            is_primary=True,
        )

    # 3. Get or Create User Profile
    profiles = profile_dao.get_profiles_for_user(str(user.user_id))
    if not any(p.name == TEST_PROFILE_NAME for p in profiles):
        logger.info(f"Creating profile for user {user.user_id}")
        profile_dao.create_profile(
            user_id=str(user.user_id),
            name=TEST_PROFILE_NAME,
            birth_datetime=datetime(1990, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            birth_location_id=None,  # For now using None - geolocation will resolve this later
            gender=Gender.MALE,
            relationship=RelationshipType.SELF,
        )

    # 4. Mock Telegram Sender and Yield Environment Details
    with patch(
        "channels.telegram.TelegramWebhookHandler.send_message", new_callable=AsyncMock
    ) as mock_send:
        logger.info("--- Test environment setup complete ---")
        yield {"telegram_user_id": TEST_TELEGRAM_ID, "mock_send_message": mock_send}

    logger.info("--- Tearing down test environment ---")
