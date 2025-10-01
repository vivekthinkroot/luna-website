"""
UserDAO implementation for Luna.
Handles user lifecycle management and multi-channel identity operations.
"""

import re
import uuid
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from data.db import get_session
from data.models import ChannelType, TUser, TUserChannel


class User(BaseModel):
    user_id: UUID
    phone: Optional[str] = None
    email: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserDAO:
    """Data access object for user operations (synchronous)."""

    @staticmethod
    def normalize_phone(phone: str) -> str:
        """
        Normalize phone number to E.164 format (basic version).
        Args:
            phone (str): Raw phone number.
        Returns:
            str: Normalized phone number.
        """
        digits = re.sub(r"\D", "", phone)
        if not digits.startswith("+"):
            digits = "+" + digits
        return digits

    def create_user(self, phone: str, email: Optional[str] = None) -> User:
        """
        Create new user with validation.
        Args:
            user_data (Dict[str, Any]): User data dict.
        Returns:
            Users: Created user object.
        Raises:
            ValueError: If user already exists or invalid data.
        """
        phone = self.normalize_phone(phone)
        now = datetime.now(timezone.utc)
        user = TUser(phone=phone, email=email, created_at=now, updated_at=now)
        with get_session() as db:
            db.add(user)
            try:
                db.commit()
                db.refresh(user)
                return User.model_validate(user)
            except IntegrityError as e:
                db.rollback()
                raise ValueError("User already exists or invalid data") from e

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """
        Get user by primary ID.
        Args:
            user_id (str): User ID.
        Returns:
            Optional[Users]: User object or None.
        """
        with get_session() as db:
            result = db.exec(select(TUser).where(TUser.user_id == user_id))
            user = result.one_or_none()
            return User.model_validate(user) if user else None

    def get_user_by_phone(self, phone: str) -> Optional[User]:
        """
        Get user by phone number.
        Args:
            phone (str): Phone number.
        Returns:
            Optional[Users]: User object or None.
        """
        phone = self.normalize_phone(phone)
        with get_session() as db:
            result = db.exec(select(TUser).where(TUser.phone == phone))
            user = result.one_or_none()
            return User.model_validate(user) if user else None

    def get_user_by_channel(
        self, channel_type: str, user_identity: str
    ) -> Optional[User]:
        """
        Get user by channel identity.
        Args:
            channel_type (str): Channel type (e.g., 'telegram').
            user_identity (str): Platform-specific user ID.
        Returns:
            Optional[Users]: User object or None.
        """
        with get_session() as db:
            result = db.exec(
                select(TUser)
                .join(TUserChannel)
                .where(
                    TUserChannel.channel_type == channel_type,
                    TUserChannel.user_identity == user_identity,
                    TUserChannel.user_id == TUser.user_id,
                )
            )
            user = result.one_or_none()
            return User.model_validate(user) if user else None

    def update_user(
        self, user_id: str, phone: Optional[str] = None, email: Optional[str] = None
    ) -> User:
        """
        Update user information.
        Args:
            user_id (str): User ID.
            updates (Dict[str, Any]): Fields to update.
        Returns:
            Users: Updated user object.
        Raises:
            ValueError: If user not found.
        """
        with get_session() as db:
            result = db.exec(select(TUser).where(TUser.user_id == user_id))
            user = result.one_or_none()
            if not user:
                raise ValueError("User not found")
            if phone is not None:
                user.phone = self.normalize_phone(phone)
            if email is not None:
                user.email = email
            user.updated_at = datetime.now(timezone.utc)
            db.add(user)
            db.commit()
            db.refresh(user)
            return User.model_validate(user)

    def link_channel(
        self,
        user_id: str,
        channel_type: ChannelType,
        user_identity: str,
        is_primary: bool = False,
    ) -> TUserChannel:
        """
        Link user to new channel.
        Args:
            user_id (str): User ID.
            channel_data (Dict[str, Any]): Channel info dict.
        Returns:
            UserChannels: Created channel link object.
        """
        # Ensure user_id is a UUID (handles both str and UUID input)
        user_id_uuid = (
            user_id if isinstance(user_id, uuid.UUID) else uuid.UUID(str(user_id))
        )
        now = datetime.now(timezone.utc)
        channel = TUserChannel(
            user_id=user_id_uuid,
            channel_type=channel_type,
            user_identity=user_identity,
            is_primary=is_primary,
            created_at=now,
        )
        with get_session() as db:
            db.add(channel)
            try:
                db.commit()
                db.refresh(channel)
                return channel
            except IntegrityError as e:
                db.rollback()
                raise ValueError("Channel link already exists or invalid data") from e

    def get_user_channels(self, user_id: str) -> List[TUserChannel]:
        """
        Get all channels for user.
        Args:
            user_id (str): User ID.
        Returns:
            List[UserChannels]: List of channel link objects.
        """
        with get_session() as db:
            result = db.exec(
                select(TUserChannel).where(TUserChannel.user_id == user_id)
            )
            return list(result.all())
