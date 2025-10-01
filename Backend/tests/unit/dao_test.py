from datetime import datetime, timezone

import pytest
from sqlalchemy import text

from dao.conversations import ConversationDAO
from dao.notifications import NotificationDAO
from dao.profiles import ProfileDAO
from dao.users import UserDAO
from data.db import get_session
from data.models import (
    ChannelType,
    Gender,
    MessageType,
    NotificationFrequency,
    NotificationType,
)

# Helper to clean up all test data by unique marker
TEST_MARKER = "test_marker"

# Track inserted IDs for cleanup
inserted_user_ids = set()
inserted_channel_ids = set()
inserted_profile_ids = set()
inserted_profile_link_keys = set()  # (profile_id, user_id)
inserted_profile_data_ids = set()
inserted_notification_pref_ids = set()
inserted_conversation_ids = set()


def cleanup_test_data():
    with get_session() as db:
        # Conversations
        for msg_id in inserted_conversation_ids:
            db.execute(
                text("DELETE FROM conversations WHERE message_id = :msg_id"),
                {"msg_id": msg_id},
            )
        # Notification preferences
        for pref_id in inserted_notification_pref_ids:
            db.execute(
                text(
                    "DELETE FROM notification_preferences WHERE preference_id = :pref_id"
                ),
                {"pref_id": str(pref_id)},
            )
        # Profile data
        for profile_id in inserted_profile_data_ids:
            db.execute(
                text("DELETE FROM profile_data WHERE profile_id = :profile_id"),
                {"profile_id": str(profile_id)},
            )
        # User-profile links
        for profile_id, user_id in inserted_profile_link_keys:
            db.execute(
                text(
                    "DELETE FROM user_profile_links WHERE profile_id = :profile_id AND user_id = :user_id"
                ),
                {"profile_id": str(profile_id), "user_id": str(user_id)},
            )
        # Profiles
        for profile_id in inserted_profile_ids:
            db.execute(
                text("DELETE FROM profiles WHERE profile_id = :profile_id"),
                {"profile_id": str(profile_id)},
            )
        # User channels
        for channel_id in inserted_channel_ids:
            db.execute(
                text("DELETE FROM user_channels WHERE channel_id = :channel_id"),
                {"channel_id": str(channel_id)},
            )
        # Users
        for user_id in inserted_user_ids:
            db.execute(
                text("DELETE FROM users WHERE user_id = :user_id"),
                {"user_id": str(user_id)},
            )
        db.commit()


@pytest.fixture(scope="module", autouse=True)
def setup_and_teardown():
    cleanup_test_data()
    yield
    cleanup_test_data()


def test_user_dao():
    user_dao = UserDAO()
    phone = "+9990000001"
    email = "test-user1@example.com"
    # Create user
    user = user_dao.create_user(phone, email)
    inserted_user_ids.add(str(user.user_id))
    assert user.user_id
    assert user.phone == phone
    assert user.email == email
    assert user.created_at and user.updated_at

    # Get by id
    fetched = user_dao.get_user_by_id(str(user.user_id))
    assert fetched and fetched.user_id == user.user_id

    # Get by phone
    fetched2 = user_dao.get_user_by_phone(phone)
    assert fetched2 and fetched2.user_id == user.user_id

    # Update user
    new_email = "test-user1b@example.com"
    updated = user_dao.update_user(str(user.user_id), email=new_email)
    assert updated.email == new_email
    assert updated.updated_at > updated.created_at

    # Link telegram channel
    channel_telegram = user_dao.link_channel(
        str(user.user_id), ChannelType.TELEGRAM, "test-telegram-1", is_primary=True
    )
    inserted_channel_ids.add(str(channel_telegram.channel_id))
    assert channel_telegram.channel_id
    assert channel_telegram.user_id == user.user_id
    assert channel_telegram.created_at

    # Link whatsapp channel for the same user
    channel_whatsapp = user_dao.link_channel(
        str(user.user_id), ChannelType.WHATSAPP, "test-whatsapp-1", is_primary=False
    )
    inserted_channel_ids.add(str(channel_whatsapp.channel_id))
    assert channel_whatsapp.channel_id
    assert channel_whatsapp.user_id == user.user_id
    assert channel_whatsapp.created_at

    # Get user channels
    channels = user_dao.get_user_channels(str(user.user_id))
    assert any(c.channel_id == channel_telegram.channel_id for c in channels)
    assert any(c.channel_id == channel_whatsapp.channel_id for c in channels)


def test_profile_dao():
    profile_dao = ProfileDAO()
    user_dao = UserDAO()
    # Create user for profile
    user = user_dao.create_user("+9990000002", "test-user2@example.com")
    inserted_user_ids.add(str(user.user_id))
    # Create profile for user (minimal fields)
    profile = profile_dao.create_profile(
        user_id=str(user.user_id),
        name="TestUser2",
        birth_datetime=datetime(2000, 1, 1, tzinfo=timezone.utc),
        birth_location_id=None,  # For now using None - geolocation will resolve this later
        gender=Gender.MALE,
    )
    inserted_profile_ids.add(str(profile.profile_id))
    assert profile.profile_id
    assert profile.created_at and profile.updated_at
    assert profile.name == "TestUser2"
    assert profile.birth_location_id is None
    assert profile.gender == Gender.MALE

    # Get by id
    fetched = profile_dao.get_profile_by_id(str(profile.profile_id))
    assert fetched and fetched.profile_id == profile.profile_id
    assert fetched.name == "TestUser2"

    # Update profile
    updated = profile_dao.update_profile(
        str(profile.profile_id), name="TestUser2b", birth_location_id=123
    )
    assert updated.name == "TestUser2b"
    assert updated.birth_location_id == 123
    assert updated.updated_at > updated.created_at

    # Get all profiles for user
    profiles = profile_dao.get_profiles_for_user(str(user.user_id))
    assert any(p.profile_id == profile.profile_id for p in profiles)
    assert any(p.name == "TestUser2b" for p in profiles)


def test_notification_dao():
    notification_dao = NotificationDAO()
    profile_dao = ProfileDAO()
    user_dao = UserDAO()
    # Create user for profile
    user = user_dao.create_user("+9990000003", "test-user3@example.com")
    inserted_user_ids.add(str(user.user_id))
    # Create profile for notification
    profile = profile_dao.create_profile(
        user_id=str(user.user_id),
        name="TestUser3",
        birth_datetime=datetime(2000, 1, 2, tzinfo=timezone.utc),
        birth_location_id=None,  # Using None for test - real usage would resolve location
        gender=Gender.FEMALE,
    )
    inserted_profile_ids.add(str(profile.profile_id))
    # Create preference
    pref = notification_dao.create_preference(
        profile_id=str(profile.profile_id),
        notification_type=NotificationType.EMAIL,
        frequency=NotificationFrequency.DAILY,
        channel="test_channel",
        enabled=True,
    )
    inserted_notification_pref_ids.add(str(pref.preference_id))
    assert pref.preference_id
    assert pref.created_at and pref.updated_at

    # Update preference
    updated = notification_dao.update_preference(str(pref.preference_id), enabled=False)
    assert updated.enabled is False
    assert updated.updated_at > updated.created_at

    # Toggle preference
    toggled = notification_dao.toggle_preference(str(pref.preference_id), True)
    assert toggled.enabled is True
    assert toggled.updated_at > toggled.created_at

    # Get user/profile preferences
    user_prefs = notification_dao.get_user_preferences(str(profile.profile_id))
    assert isinstance(user_prefs, list)
    profile_prefs = notification_dao.get_profile_preferences(str(profile.profile_id))
    assert any(p.preference_id == pref.preference_id for p in profile_prefs)

    # Get active preferences
    active = notification_dao.get_active_preferences(NotificationType.EMAIL)
    assert isinstance(active, list)


def test_conversation_dao():
    conversation_dao = ConversationDAO()
    user_dao = UserDAO()
    # Create user for conversation
    user = user_dao.create_user("+9990000003", "test-user3@example.com")
    inserted_user_ids.add(str(user.user_id))
    # Save message
    msg = conversation_dao.save_message(
        user_id=str(user.user_id),
        channel=ChannelType.TELEGRAM,
        message_type=MessageType.INCOMING_TEXT,
        content="test message 1",
        additional_info={"foo": "bar"},
    )
    inserted_conversation_ids.add(msg.message_id)
    assert msg.message_id
    assert msg.created_at

    # Get by id
    fetched = conversation_dao.get_conversation_by_id(msg.message_id)
    assert fetched and fetched.message_id == msg.message_id

    # Get conversation history
    history = conversation_dao.get_conversation_history(
        str(user.user_id), ChannelType.TELEGRAM
    )
    assert any(m.message_id == msg.message_id for m in history)

    # Get user conversations
    user_convs = conversation_dao.get_user_conversations(str(user.user_id), days=1)
    assert any(m.message_id == msg.message_id for m in user_convs)

    # Clean up old conversations (should not delete just created)
    deleted = conversation_dao.cleanup_old_conversations(days=0)
    assert isinstance(deleted, int)


def test_profile_data_dao():
    profile_dao = ProfileDAO()
    user_dao = UserDAO()

    # Create user for profile
    user = user_dao.create_user("+9990000004", "test-user4@example.com")
    inserted_user_ids.add(str(user.user_id))

    # Create profile for data
    profile = profile_dao.create_profile(
        user_id=str(user.user_id),
        name="TestUser4",
        birth_datetime=datetime(2000, 1, 3, tzinfo=timezone.utc),
        birth_location_id=None,  # Using None for test
        gender=Gender.MALE,
    )
    inserted_profile_ids.add(str(profile.profile_id))

    # Test data to store
    test_kundli_data = {
        "basic_astro_details": {
            "full_name": "TestUser4",
            "sun_sign": "Capricorn",
            "moon_sign": "Aquarius",
        },
        "planetary_positions": {
            "planets": [
                {"name": "Sun", "sign": "Capricorn"},
                {"name": "Moon", "sign": "Aquarius"},
            ]
        },
    }

    # Store kundli data
    stored_data = profile_dao.store_kundli_data(
        profile_id=str(profile.profile_id), kundli_data=test_kundli_data
    )
    inserted_profile_data_ids.add(str(profile.profile_id))

    assert stored_data.profile_id == profile.profile_id
    assert stored_data.kundli_data == test_kundli_data
    assert stored_data.created_at and stored_data.updated_at

    # Get profile data
    fetched_data = profile_dao.get_profile_data(str(profile.profile_id))
    assert fetched_data is not None
    assert fetched_data.profile_id == profile.profile_id
    assert fetched_data.kundli_data == test_kundli_data

    # Update existing data
    updated_kundli_data = {**test_kundli_data, "additional_info": "Updated data"}

    updated_data = profile_dao.store_kundli_data(
        profile_id=str(profile.profile_id), kundli_data=updated_kundli_data
    )

    assert updated_data.kundli_data == updated_kundli_data
    assert updated_data.updated_at > updated_data.created_at

    # Test deletion
    deleted = profile_dao.delete_profile_data(str(profile.profile_id))
    assert deleted is True

    # Verify deletion
    fetched_after_delete = profile_dao.get_profile_data(str(profile.profile_id))
    assert fetched_after_delete is None
