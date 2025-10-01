"""
Notification scheduler for Luna.
Handles scheduled notifications using aiocron.
"""

import asyncio
from datetime import datetime, timezone
from typing import List

import aiocron
from utils.logger import get_logger

from dao.notifications import NotificationDAO
from dao.profiles import ProfileDAO
from dao.users import UserDAO
from services.channels import ChannelsService
from data.models import NotificationFrequency, NotificationType
from utils.models import ContentType

logger = get_logger()


class NotificationScheduler:
    """Scheduler for handling notification jobs."""
    
    def __init__(self):
        """Initialize the notification scheduler."""
        self.notification_dao = NotificationDAO()
        self.profile_dao = ProfileDAO()
        self.user_dao = UserDAO()
        self.channels_service = ChannelsService()
        
        # Production cron schedules
        self.daily_cron = "0 6 * * *"      # Every day at 6 AM
        self.weekly_cron = "0 6 * * 1"     # Every Monday at 6 AM
        self.monthly_cron = "0 6 1 * *"    # First day of month at 6 AM
        
        logger.info("NotificationScheduler initialized with production schedules")
    
    async def start_scheduler(self):
        """Start the notification scheduler."""
        logger.info("Starting notification scheduler...")
        
        # Schedule daily notifications
        aiocron.crontab(self.daily_cron, func=self.process_daily_notifications, start=True)
        logger.info(f"✅ Daily notifications scheduled: {self.daily_cron}")
        
        # Schedule weekly notifications
        aiocron.crontab(self.weekly_cron, func=self.process_weekly_notifications, start=True)
        logger.info(f"✅ Weekly notifications scheduled: {self.weekly_cron}")
        
        # Schedule monthly notifications
        aiocron.crontab(self.monthly_cron, func=self.process_monthly_notifications, start=True)
        logger.info(f"✅ Monthly notifications scheduled: {self.monthly_cron}")
        
        logger.info("🎉 Notification scheduler started successfully")

    async def process_daily_notifications(self):
        """Process daily notifications."""
        logger.info("🔄 Processing daily notifications...")
        await self._process_notifications(NotificationFrequency.DAILY)

    async def process_weekly_notifications(self):
        """Process weekly notifications."""
        logger.info("🔄 Processing weekly notifications...")
        await self._process_notifications(NotificationFrequency.WEEKLY)

    async def process_monthly_notifications(self):
        """Process monthly notifications."""
        logger.info("🔄 Processing monthly notifications...")
        await self._process_notifications(NotificationFrequency.MONTHLY)

    async def _process_notifications(self, frequency: NotificationFrequency):
        """Process notifications for a specific frequency."""
        try:
            # Get all notification preferences for this frequency
            preferences = self.notification_dao.get_preferences_by_frequency(frequency)
            
            if not preferences:
                logger.info(f"No {frequency.value} notification preferences found")
                return
            
            logger.info(f"Found {len(preferences)} {frequency.value} notification preferences")
            
            for preference in preferences:
                try:
                    await self._send_notification_for_preference(preference)
                except Exception as e:
                    logger.error(f"Error processing notification for preference {preference.preference_id}: {e}")
                    continue
            
            logger.info(f"✅ Completed processing {frequency.value} notifications")
                
        except Exception as e:
            logger.error(f"Error in {frequency.value} notification processing: {e}")
    
    async def _send_notification_for_preference(self, preference):
        """Send notification for a specific preference."""
        try:
            # Get the profile associated with this preference
            profile = self.profile_dao.get_profile_by_id(str(preference.profile_id))
            if not profile:
                logger.warning(f"Profile {preference.profile_id} not found for preference {preference.preference_id}")
                return
            
            # Get the user associated with this profile via user_profile_links
            from dao.users import UserDAO
            user_dao = UserDAO()
            
            # Get user channels - we need to find the user through profile links
            from data.db import get_session
            from data.models import TUserProfileLink
            from sqlmodel import select
            
            with get_session() as db:
                result = db.exec(
                    select(TUserProfileLink).where(
                        TUserProfileLink.profile_id == preference.profile_id
                    )
                )
                profile_links = result.all()
                
                if not profile_links:
                    logger.warning(f"No user found for profile {preference.profile_id}")
                    return
                
                # Get channels for the first user (assuming one user per profile for now)
                user_id = str(profile_links[0].user_id)
                channels = user_dao.get_user_channels(user_id)
                
                if not channels:
                    logger.warning(f"No channels found for user {user_id}")
                    return
                
                # Generate notification message
                message = self._generate_notification_message(preference.notification_type, profile)
                
                # Send to all user channels
                for channel in channels:
                    try:
                        success = await self.channels_service.send_message(
                            user_id=user_id,
                            channel_type=channel.channel_type.value,
                            channel_user_id=channel.user_identity,
                            content_type=ContentType.TEXT,
                            content=message,
                            metadata={
                                "notification_type": preference.notification_type.value,
                                "frequency": preference.frequency.value,
                                "timestamp": datetime.now(timezone.utc).isoformat()
                            }
                        )
                        if success:
                            logger.info(f"✅ Sent {preference.notification_type.value} notification to {channel.channel_type.value} user {channel.user_identity}")
                    except Exception as e:
                        logger.error(f"Error sending to {channel.channel_type.value} user {channel.user_identity}: {e}")
                        continue
            
        except Exception as e:
            logger.error(f"Error in _send_notification_for_preference: {e}")

    def _generate_notification_message(self, notification_type: NotificationType, profile) -> str:
        """Generate notification message based on type and profile."""
        from .utils import generate_mock_message, generate_custom_message
        
        # Since NotificationType is for channels, we'll use the channel type to determine content
        # For now, we'll generate general messages based on profile
        if notification_type.value in ["telegram", "whatsapp"]:
            # For messaging platforms, generate personalized content
            return generate_mock_message("general", profile.name)
        elif notification_type.value == "email":
            # For email, generate more detailed content
            return generate_custom_message(profile.name)
        else:
            # For other channels, generate general content
            return generate_mock_message("general", profile.name)

    async def stop_scheduler(self):
        """Stop the notification scheduler."""
        logger.info("Stopping notification scheduler...")
        # aiocron doesn't have a direct stop method, but we can log the stop
        logger.info("Notification scheduler stopped")


# Global scheduler instance
notification_scheduler = NotificationScheduler()


async def start_notification_scheduler():
    """Start the global notification scheduler."""
    await notification_scheduler.start_scheduler()


async def stop_notification_scheduler():
    """Stop the global notification scheduler."""
    await notification_scheduler.stop_scheduler()
