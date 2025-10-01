"""
Notification service for Luna.
Provides high-level interface for notification operations.
"""

from typing import List, Optional
from datetime import datetime, timezone

from dao.notifications import NotificationDAO, NotificationPreference
from dao.profiles import ProfileDAO
from dao.users import UserDAO
from services.channels import ChannelsService
from data.models import NotificationFrequency, NotificationType
from utils.logger import get_logger
from utils.models import ContentType
from .utils import generate_mock_message, generate_custom_message

logger = get_logger()


class NotificationService:
    """Service for managing notifications."""

    def __init__(self):
        """Initialize the notification service."""
        self.notification_dao = NotificationDAO()
        self.profile_dao = ProfileDAO()
        self.user_dao = UserDAO()
        self.channels_service = ChannelsService()

    async def send_simple_test_notification(
        self, 
        user_id: str, 
        message_type: str = "general",
        channel_type: str = "telegram"
    ) -> bool:
        """
        Send a simple test notification without LLMs.
        
        Args:
            user_id (str): User ID
            message_type (str): Type of message (horoscope, tarot, numerology, general)
            channel_type (str): Channel type (default: telegram)
            
        Returns:
            bool: Success status
        """
        try:
            # Get user channels
            channels = self.user_dao.get_user_channels(user_id)
            if not channels:
                logger.warning(f"No channels found for user {user_id}")
                return False
            
            # Get user's first profile for personalization
            profiles = self.profile_dao.get_profiles_for_user(user_id)
            profile_name = profiles[0].name if profiles else None
            
            # Generate simple message
            message = generate_mock_message(message_type, profile_name)
            
            # Send to specified channel
            for channel in channels:
                if channel.channel_type.value.lower() == channel_type.lower():
                    success = await self.channels_service.send_message(
                        user_id=user_id,
                        channel_type=channel.channel_type.value,
                        channel_user_id=channel.user_identity,
                        content_type=ContentType.TEXT,
                        content=message,
                        metadata={
                            "notification_type": "simple_test",
                            "message_type": message_type,
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        }
                    )
                    if success:
                        logger.info(f"✅ Simple test {message_type} notification sent to user {user_id}")
                        return True
            
            logger.warning(f"No {channel_type} channel found for user {user_id}")
            return False
            
        except Exception as e:
            logger.error(f"Error sending simple test notification: {e}")
            return False

    async def send_test_notification(
        self, 
        user_id: str, 
        notification_type: NotificationType,
        channel_type: str = "telegram"
    ) -> bool:
        """
        Send a test notification to a user.
        
        Args:
            user_id (str): User ID
            notification_type (NotificationType): Type of notification
            channel_type (str): Channel type (default: telegram)
            
        Returns:
            bool: Success status
        """
        try:
            # Get user channels
            channels = self.user_dao.get_user_channels(user_id)
            if not channels:
                logger.warning(f"No channels found for user {user_id}")
                return False
            
            # Get user's first profile for personalization
            profiles = self.profile_dao.get_profiles_for_user(user_id)
            profile_name = profiles[0].name if profiles else None
            
            # Generate message
            message = self._generate_message(notification_type, profile_name)
            
            # Send to specified channel
            for channel in channels:
                if channel.channel_type.value.lower() == channel_type.lower():
                    success = await self.channels_service.send_message(
                        user_id=user_id,
                        channel_type=channel.channel_type.value,
                        channel_user_id=channel.user_identity,
                        content_type=ContentType.TEXT,
                        content=message,
                        metadata={
                            "notification_type": notification_type.value,
                            "test": True,
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        }
                    )
                    if success:
                        logger.info(f"✅ Test {notification_type.value} notification sent to user {user_id}")
                        return True
            
            logger.warning(f"No {channel_type} channel found for user {user_id}")
            return False
            
        except Exception as e:
            logger.error(f"Error sending test notification: {e}")
            return False

    async def send_immediate_notification(
        self,
        user_id: str,
        message: str,
        channel_type: str = "telegram"
    ) -> bool:
        """
        Send an immediate custom notification to a user.
        
        Args:
            user_id (str): User ID
            message (str): Custom message
            channel_type (str): Channel type (default: telegram)
            
        Returns:
            bool: Success status
        """
        try:
            # Get user channels
            channels = self.user_dao.get_user_channels(user_id)
            if not channels:
                logger.warning(f"No channels found for user {user_id}")
                return False
            
            # Send to specified channel
            for channel in channels:
                if channel.channel_type.value.lower() == channel_type.lower():
                    success = await self.channels_service.send_message(
                        user_id=user_id,
                        channel_type=channel.channel_type.value,
                        channel_user_id=channel.user_identity,
                        content_type=ContentType.TEXT,
                        content=message,
                        metadata={
                            "notification_type": "immediate",
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        }
                    )
                    if success:
                        logger.info(f"✅ Immediate notification sent to user {user_id}")
                        return True
            
            logger.warning(f"No {channel_type} channel found for user {user_id}")
            return False
            
        except Exception as e:
            logger.error(f"Error sending immediate notification: {e}")
            return False

    def create_notification_preference(
        self,
        profile_id: str,
        notification_type: NotificationType,
        frequency: NotificationFrequency,
        channel: str = "telegram",
        enabled: bool = True
    ) -> NotificationPreference:
        """
        Create a notification preference.
        
        Args:
            profile_id (str): Profile ID
            notification_type (NotificationType): Type of notification
            frequency (NotificationFrequency): Frequency of notifications
            channel (str): Channel type (default: telegram)
            enabled (bool): Whether preference is enabled (default: True)
            
        Returns:
            NotificationPreference: Created preference
        """
        try:
            preference = self.notification_dao.create_preference(
                profile_id=profile_id,
                notification_type=notification_type,
                frequency=frequency,
                channel=channel,
                enabled=enabled
            )
            logger.info(f"✅ Created notification preference for profile {profile_id}")
            return preference
        except Exception as e:
            logger.error(f"Error creating notification preference: {e}")
            raise

    def get_user_notification_preferences(self, user_id: str) -> List[NotificationPreference]:
        """
        Get all notification preferences for a user.
        
        Args:
            user_id (str): User ID
            
        Returns:
            List[NotificationPreference]: List of preferences
        """
        try:
            # Get user's profiles
            profiles = self.profile_dao.get_profiles_for_user(user_id)
            if not profiles:
                return []
            
            # Get preferences for each profile
            all_preferences = []
            for profile in profiles:
                preferences = self.notification_dao.get_profile_preferences(str(profile.profile_id))
                all_preferences.extend(preferences)
            
            return all_preferences
        except Exception as e:
            logger.error(f"Error getting user notification preferences: {e}")
            return []

    def update_notification_preference(
        self,
        preference_id: str,
        frequency: Optional[NotificationFrequency] = None,
        channel: Optional[str] = None,
        enabled: Optional[bool] = None
    ) -> NotificationPreference:
        """
        Update a notification preference.
        
        Args:
            preference_id (str): Preference ID
            frequency (Optional[NotificationFrequency]): New frequency
            channel (Optional[str]): New channel
            enabled (Optional[bool]): New enabled status
            
        Returns:
            NotificationPreference: Updated preference
        """
        try:
            preference = self.notification_dao.update_preference(
                preference_id=preference_id,
                frequency=frequency,
                channel=channel,
                enabled=enabled
            )
            logger.info(f"✅ Updated notification preference {preference_id}")
            return preference
        except Exception as e:
            logger.error(f"Error updating notification preference: {e}")
            raise

    def toggle_notification_preference(
        self,
        preference_id: str,
        enabled: bool
    ) -> NotificationPreference:
        """
        Toggle a notification preference on/off.
        
        Args:
            preference_id (str): Preference ID
            enabled (bool): New enabled status
            
        Returns:
            NotificationPreference: Updated preference
        """
        try:
            preference = self.notification_dao.toggle_preference(
                preference_id=preference_id,
                enabled=enabled
            )
            status = "enabled" if enabled else "disabled"
            logger.info(f"✅ {status.capitalize()} notification preference {preference_id}")
            return preference
        except Exception as e:
            logger.error(f"Error toggling notification preference: {e}")
            raise

    def _generate_message(self, notification_type: NotificationType, profile_name: Optional[str] = None) -> str:
        """Generate message based on notification type."""
        # Since NotificationType is for channels, we'll generate general content
        # In a real implementation, you might have separate content types
        return generate_mock_message("general", profile_name)
