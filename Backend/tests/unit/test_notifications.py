"""
Unit tests for notifications module.
"""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

from notifications import NotificationScheduler, NotificationService
from notifications.utils import generate_mock_message, generate_custom_message
from data.models import NotificationFrequency, NotificationType
from dao.notifications import NotificationPreference


class TestNotificationUtils:
    """Test notification utility functions."""

    def test_generate_mock_message_horoscope(self):
        """Test generating horoscope message."""
        message = generate_mock_message("horoscope", "John")
        # Check for horoscope-related content (no name checking)
        assert any(keyword in message.lower() for keyword in ["horoscope", "prediction", "reading"])

    def test_generate_mock_message_tarot(self):
        """Test generating tarot message."""
        message = generate_mock_message("tarot", "Jane")
        # Check for tarot-related content (no name checking)
        assert any(keyword in message.lower() for keyword in ["tarot", "cards", "reading", "prediction"])

    def test_generate_mock_message_numerology(self):
        """Test generating numerology message."""
        message = generate_mock_message("numerology", "Bob")
        # Check for numerology-related content (no name checking)
        assert any(keyword in message.lower() for keyword in ["numerology", "reading", "prediction", "guidance"])

    def test_generate_mock_message_general(self):
        """Test generating general message."""
        message = generate_mock_message("general", "Alice")
        # Check for general prediction content (no name checking)
        assert any(keyword in message.lower() for keyword in ["prediction", "reading", "forecast", "guidance"])

    def test_generate_mock_message_no_name(self):
        """Test generating message without name."""
        message = generate_mock_message("general")
        # Should work the same as with name since names are not used
        assert any(keyword in message.lower() for keyword in ["prediction", "reading", "forecast", "guidance"])

    def test_generate_custom_message(self):
        """Test generating custom message."""
        message = generate_custom_message("Charlie")
        # Check for personalized content (no name checking)
        assert any(keyword in message.lower() for keyword in ["personalized", "custom", "prediction", "reading"])


class TestNotificationService:
    """Test notification service."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = NotificationService()

    @patch('notifications.service.UserDAO')
    @patch('notifications.service.ProfileDAO')
    @patch('notifications.service.ChannelsService')
    def test_create_notification_preference(self, mock_channels_service, mock_profile_dao, mock_user_dao):
        """Test creating notification preference."""
        # Mock the DAO
        mock_notification_dao = MagicMock()
        self.service.notification_dao = mock_notification_dao
        
        # Mock the created preference
        mock_preference = MagicMock()
        mock_notification_dao.create_preference.return_value = mock_preference
        
        # Test
        result = self.service.create_notification_preference(
            profile_id="test-profile-123",
            notification_type=NotificationType.TELEGRAM,
            frequency=NotificationFrequency.DAILY,
            channel="telegram",
            enabled=True
        )
        
        # Assertions
        assert result == mock_preference
        mock_notification_dao.create_preference.assert_called_once_with(
            profile_id="test-profile-123",
            notification_type=NotificationType.TELEGRAM,
            frequency=NotificationFrequency.DAILY,
            channel="telegram",
            enabled=True
        )

    @patch('notifications.service.UserDAO')
    @patch('notifications.service.ProfileDAO')
    def test_get_user_notification_preferences(self, mock_profile_dao, mock_user_dao):
        """Test getting user notification preferences."""
        # Mock the DAOs
        mock_notification_dao = MagicMock()
        self.service.notification_dao = mock_notification_dao
        
        # Mock profiles with proper UUID
        import uuid
        mock_profile = MagicMock()
        mock_profile.profile_id = uuid.uuid4()
        
        # Mock the ProfileDAO instance
        mock_profile_instance = MagicMock()
        mock_profile_instance.get_profiles_for_user.return_value = [mock_profile]
        self.service.profile_dao = mock_profile_instance
        
        # Mock preferences
        mock_preference = MagicMock()
        mock_notification_dao.get_profile_preferences.return_value = [mock_preference]
        
        # Test
        result = self.service.get_user_notification_preferences("test-user-123")
        
        # Assertions
        assert len(result) == 1
        assert result[0] == mock_preference
        mock_notification_dao.get_profile_preferences.assert_called_once_with(str(mock_profile.profile_id))


class TestNotificationScheduler:
    """Test notification scheduler."""

    def setup_method(self):
        """Set up test fixtures."""
        self.scheduler = NotificationScheduler()

    def test_scheduler_initialization(self):
        """Test scheduler initialization."""
        assert self.scheduler.daily_cron == "0 6 * * *"
        assert self.scheduler.weekly_cron == "0 6 * * 1"
        assert self.scheduler.monthly_cron == "0 6 1 * *"

    @patch('notifications.notifications_job.aiocron.crontab')
    async def test_start_scheduler(self, mock_crontab):
        """Test starting the scheduler."""
        await self.scheduler.start_scheduler()
        
        # Verify cron jobs were created
        assert mock_crontab.call_count == 3

    def test_generate_notification_message(self):
        """Test generating notification message."""
        # Mock profile
        mock_profile = MagicMock()
        mock_profile.name = "Test User"
        
        # Test with different notification types
        message1 = self.scheduler._generate_notification_message(NotificationType.TELEGRAM, mock_profile)
        message2 = self.scheduler._generate_notification_message(NotificationType.EMAIL, mock_profile)
        
        # Assertions - messages should be generated but no names expected
        assert len(message1) > 0
        assert len(message2) > 0
        # Check that messages contain prediction-related content
        assert any(keyword in message1.lower() for keyword in ["prediction", "reading", "forecast", "guidance"])
        assert any(keyword in message2.lower() for keyword in ["prediction", "reading", "forecast", "guidance"])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
