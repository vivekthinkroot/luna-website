"""
NotificationDAO implementation for Luna.
Handles notification preference management and channel-specific operations.
"""

import uuid
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from data.db import get_session
from data.models import NotificationFrequency, NotificationType, TNotificationPreference


class NotificationPreference(BaseModel):
    preference_id: UUID
    profile_id: UUID
    notification_type: NotificationType
    frequency: NotificationFrequency
    channel: str
    enabled: bool = True
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class NotificationDAO:
    """Data access object for notification preference operations (synchronous)."""

    def create_preference(
        self,
        profile_id: str,
        notification_type: NotificationType,
        frequency: NotificationFrequency,
        channel: str,
        enabled: bool = True,
    ) -> NotificationPreference:
        """
        Create notification preference.
        Args:
            preference_data (Dict[str, Any]): Preference data dict.
        Returns:
            NotificationPreferences: Created preference object.
        Raises:
            ValueError: If preference already exists or invalid data.
        """
        now = datetime.now(timezone.utc)
        profile_id_uuid = (
            profile_id
            if isinstance(profile_id, uuid.UUID)
            else uuid.UUID(str(profile_id))
        )
        preference = TNotificationPreference(
            profile_id=profile_id_uuid,
            notification_type=notification_type,
            frequency=frequency,
            channel=channel,
            enabled=enabled,
            created_at=now,
            updated_at=now,
        )
        with get_session() as db:
            db.add(preference)
            try:
                db.commit()
                db.refresh(preference)
                return NotificationPreference.model_validate(preference)
            except IntegrityError as e:
                db.rollback()
                raise ValueError("Preference already exists or invalid data") from e

    def get_user_preferences(self, user_id: str) -> List[NotificationPreference]:
        """
        Get all preferences for user.
        Args:
            user_id (str): User ID.
        Returns:
            List[NotificationPreferences]: List of preference objects.
        """
        user_id_uuid = (
            user_id if isinstance(user_id, uuid.UUID) else uuid.UUID(str(user_id))
        )
        with get_session() as db:
            result = db.exec(
                select(TNotificationPreference).where(
                    TNotificationPreference.profile_id == user_id_uuid
                )
            )
            return [NotificationPreference.model_validate(p) for p in result.all()]

    def get_profile_preferences(self, profile_id: str) -> List[NotificationPreference]:
        """
        Get preferences for specific profile.
        Args:
            profile_id (str): Profile ID.
        Returns:
            List[NotificationPreferences]: List of preference objects.
        """
        profile_id_uuid = (
            profile_id
            if isinstance(profile_id, uuid.UUID)
            else uuid.UUID(str(profile_id))
        )
        with get_session() as db:
            result = db.exec(
                select(TNotificationPreference).where(
                    TNotificationPreference.profile_id == profile_id_uuid
                )
            )
            return [NotificationPreference.model_validate(p) for p in result.all()]

    def update_preference(
        self,
        preference_id: str,
        frequency: Optional[NotificationFrequency] = None,
        channel: Optional[str] = None,
        enabled: Optional[bool] = None,
    ) -> NotificationPreference:
        """
        Update notification preference.
        Args:
            preference_id (str): Preference ID.
            updates (Dict[str, Any]): Fields to update.
        Returns:
            NotificationPreferences: Updated preference object.
        Raises:
            ValueError: If preference not found.
        """
        preference_id_uuid = (
            preference_id
            if isinstance(preference_id, uuid.UUID)
            else uuid.UUID(str(preference_id))
        )
        with get_session() as db:
            result = db.exec(
                select(TNotificationPreference).where(
                    TNotificationPreference.preference_id == preference_id_uuid
                )
            )
            preference = result.one_or_none()
            if not preference:
                raise ValueError("Preference not found")
            if frequency is not None:
                preference.frequency = frequency
            if channel is not None:
                preference.channel = channel
            if enabled is not None:
                preference.enabled = enabled
            preference.updated_at = datetime.now(timezone.utc)
            db.add(preference)
            db.commit()
            db.refresh(preference)
            return NotificationPreference.model_validate(preference)

    def toggle_preference(
        self, preference_id: str, enabled: bool
    ) -> NotificationPreference:
        """
        Enable/disable preference.
        Args:
            preference_id (str): Preference ID.
            enabled (bool): Enable or disable.
        Returns:
            NotificationPreferences: Updated preference object.
        Raises:
            ValueError: If preference not found.
        """
        preference_id_uuid = (
            preference_id
            if isinstance(preference_id, uuid.UUID)
            else uuid.UUID(str(preference_id))
        )
        with get_session() as db:
            result = db.exec(
                select(TNotificationPreference).where(
                    TNotificationPreference.preference_id == preference_id_uuid
                )
            )
            preference = result.one_or_none()
            if not preference:
                raise ValueError("Preference not found")
            preference.enabled = enabled
            preference.updated_at = datetime.now(timezone.utc)
            db.add(preference)
            db.commit()
            db.refresh(preference)
            return NotificationPreference.model_validate(preference)

    def get_active_preferences(
        self, notification_type: str
    ) -> List[NotificationPreference]:
        """
        Get all active preferences for notification type.
        Args:
            notification_type (str): Notification type.
        Returns:
            List[NotificationPreferences]: List of active preference objects.
        """
        with get_session() as db:
            result = db.exec(
                select(TNotificationPreference).where(
                    TNotificationPreference.notification_type == notification_type,
                    TNotificationPreference.enabled,
                    #TNotificationPreference.enabled == True,[ ruff suggested this linting fix]
                )
            )
            return [NotificationPreference.model_validate(p) for p in result.all()]

    def get_preferences_by_frequency(
        self, frequency: NotificationFrequency
    ) -> List[NotificationPreference]:
        """
        Get all preferences for a specific frequency.
        Args:
            frequency (NotificationFrequency): Frequency to filter by.
        Returns:
            List[NotificationPreference]: List of preference objects.
        """
        with get_session() as db:
            result = db.exec(
                select(TNotificationPreference).where(
                    TNotificationPreference.frequency == frequency,
                    TNotificationPreference.enabled == True,
                )
            )
            return [NotificationPreference.model_validate(p) for p in result.all()]
