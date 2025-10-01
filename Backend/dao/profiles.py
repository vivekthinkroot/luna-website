"""
ProfileDAO implementation for Luna.
Handles multi-profile management, birth data validation, and astrology data caching.
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from data.db import get_session
from data.models import (
    Gender,
    HouseSign,
    RelationshipType,
    TProfile,
    TProfileData,
    TUserProfileLink,
)


class Profile(BaseModel):
    profile_id: UUID
    name: Optional[str] = None
    birth_datetime: Optional[datetime] = None
    birth_place: Optional[str] = None
    birth_location_id: Optional[int] = None
    gender: Optional[Gender] = None
    sun_sign: Optional[HouseSign] = None
    moon_sign: Optional[HouseSign] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProfileData(BaseModel):
    """Profile data model for astrology information."""

    profile_id: UUID
    kundli_data: Dict[str, Any]
    horoscope_chart: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProfileDAO:
    """Data access object for profile operations (synchronous, minimal)."""

    def create_profile(
        self,
        user_id: str,
        name: Optional[str] = None,
        birth_datetime: Optional[datetime] = None,
        birth_place: Optional[str] = None,
        birth_location_id: Optional[int] = None,
        gender: Optional[Gender] = None,
        sun_sign: Optional[HouseSign] = None,
        moon_sign: Optional[HouseSign] = None,
        relationship: Optional[RelationshipType] = RelationshipType.OTHER,
    ) -> Profile:
        """
        Create a new profile and link it to a user.
        Args:
            user_id (str): User ID to link profile to.
            name, birth_datetime, birth_place, birth_location_id, gender, sun_sign, moon_sign: Profile fields (optional).
            relationship (RelationshipType): Relationship type for link (default: OTHER).
        Returns:
            Profile: Created profile object.
        Raises:
            ValueError: If creation fails.
        """
        now = datetime.now(timezone.utc)
        profile = TProfile(
            name=name,
            birth_datetime=birth_datetime,
            birth_place=birth_place,
            birth_location_id=birth_location_id,
            gender=gender,
            sun_sign=sun_sign,
            moon_sign=moon_sign,
            created_at=now,
            updated_at=now,
        )
        user_id_uuid = (
            user_id if isinstance(user_id, uuid.UUID) else uuid.UUID(str(user_id))
        )
        with get_session() as db:
            db.add(profile)
            try:
                db.commit()
                db.refresh(profile)
            except IntegrityError as e:
                db.rollback()
                raise ValueError("Profile already exists or invalid data") from e
            # Link profile to user
            link = TUserProfileLink(
                profile_id=profile.profile_id,
                user_id=user_id_uuid,
                relationship_type=(
                    relationship if relationship else RelationshipType.OTHER
                ),
                created_at=now,
            )
            db.add(link)
            try:
                db.commit()
            except IntegrityError as e:
                db.rollback()
                raise ValueError("Profile link already exists or invalid data") from e
            return Profile.model_validate(profile)

    def update_profile(
        self,
        profile_id: str,
        name: Optional[str] = None,
        birth_datetime: Optional[datetime] = None,
        birth_place: Optional[str] = None,
        birth_location_id: Optional[int] = None,
        gender: Optional[Gender] = None,
        sun_sign: Optional[HouseSign] = None,
        moon_sign: Optional[HouseSign] = None,
    ) -> Profile:
        """
        Update profile information.
        Args:
            profile_id (str): Profile ID.
            name, birth_datetime, birth_place, birth_location_id, gender, sun_sign, moon_sign: Fields to update (optional).
        Returns:
            Profile: Updated profile object.
        Raises:
            ValueError: If profile not found.
        """
        profile_id_uuid = (
            profile_id
            if isinstance(profile_id, uuid.UUID)
            else uuid.UUID(str(profile_id))
        )
        with get_session() as db:
            result = db.exec(
                select(TProfile).where(TProfile.profile_id == profile_id_uuid)
            )
            profile = result.one_or_none()
            if not profile:
                raise ValueError("Profile not found")
            if name is not None:
                profile.name = name
            if birth_datetime is not None:
                profile.birth_datetime = birth_datetime
            if birth_place is not None:
                profile.birth_place = birth_place
            if birth_location_id is not None:
                profile.birth_location_id = birth_location_id
            if gender is not None:
                profile.gender = gender
            if sun_sign is not None:
                profile.sun_sign = sun_sign
            if moon_sign is not None:
                profile.moon_sign = moon_sign
            profile.updated_at = datetime.now(timezone.utc)
            db.add(profile)
            db.commit()
            db.refresh(profile)
            return Profile.model_validate(profile)

    def get_profile_by_id(self, profile_id: str) -> Optional[Profile]:
        """
        Get profile by ID.
        Args:
            profile_id (str): Profile ID.
        Returns:
            Optional[ProfileRead]: Profile object or None.
        """
        profile_id_uuid = (
            profile_id
            if isinstance(profile_id, uuid.UUID)
            else uuid.UUID(str(profile_id))
        )
        with get_session() as db:
            result = db.exec(
                select(TProfile).where(TProfile.profile_id == profile_id_uuid)
            )
            profile = result.one_or_none()
            return Profile.model_validate(profile) if profile else None

    def get_profiles_for_user(self, user_id: str) -> List[Profile]:
        """
        Get all profiles for a user.
        Args:
            user_id (str): User ID.
        Returns:
            List[Profile]: List of profile objects.
        """
        user_id_uuid = (
            user_id if isinstance(user_id, uuid.UUID) else uuid.UUID(str(user_id))
        )
        with get_session() as db:
            result = db.exec(
                select(TProfile)
                .join(TUserProfileLink)
                .where(TUserProfileLink.user_id == user_id_uuid)
            )
            return [Profile.model_validate(p) for p in result.all()]

    def get_default_profile_for_user(self, user_id: str) -> Optional[Profile]:
        """
        Get the default profile for a user.
        Default is defined as:
            - The profile linked with relationship_type == RelationshipType.SELF, if present.
            - If only one profile is linked to the user, return that profile.
            - Otherwise, return None.
        Args:
            user_id (str): User ID.
        Returns:
            Optional[Profile]: The default profile or None.
        """
        user_id_uuid = (
            user_id if isinstance(user_id, uuid.UUID) else uuid.UUID(str(user_id))
        )
        with get_session() as db:
            # Get all profile links for the user
            result = db.exec(
                select(TUserProfileLink, TProfile)
                .join(TProfile)
                .where(TUserProfileLink.user_id == user_id_uuid)
            )
            links_and_profiles = result.all()
            if not links_and_profiles:
                return None

            # If only one profile, return it
            if len(links_and_profiles) == 1:
                _, profile = links_and_profiles[0]
                return Profile.model_validate(profile)

            # Find 'self' relationship
            for link, profile in links_and_profiles:
                if link.relationship_type == RelationshipType.SELF:
                    return Profile.model_validate(profile)

            # Otherwise, no default
            return None

    def store_kundli_data(
        self,
        profile_id: str,
        kundli_data: Dict[str, Any],
        horoscope_chart: Optional[Dict[str, Any]] = None,
    ) -> ProfileData:
        """
        Store kundli data for a profile.

        Args:
            profile_id: ID of the profile to store data for
            kundli_data: The astrological data to store
            horoscope_chart: Optional horoscope chart data

        Returns:
            ProfileData: The stored profile data object

        Raises:
            ValueError: If storage fails
        """
        profile_id_uuid = (
            profile_id if isinstance(profile_id, UUID) else UUID(str(profile_id))
        )

        now = datetime.now(timezone.utc)

        with get_session() as db:
            # Check if profile data already exists
            existing = db.exec(
                select(TProfileData).where(TProfileData.profile_id == profile_id_uuid)
            ).one_or_none()

            if existing:
                # Update existing record
                existing.kundli_data = kundli_data
                if horoscope_chart is not None:
                    existing.horoscope_chart = horoscope_chart
                existing.updated_at = now
                db.add(existing)
                try:
                    db.commit()
                    db.refresh(existing)
                    return ProfileData.model_validate(existing)
                except IntegrityError as e:
                    db.rollback()
                    raise ValueError(f"Failed to update profile data: {e}") from e
            else:
                # Create new record
                profile_data = TProfileData(
                    profile_id=profile_id_uuid,
                    kundli_data=kundli_data,
                    horoscope_chart=horoscope_chart,
                    created_at=now,
                    updated_at=now,
                )
                db.add(profile_data)
                try:
                    db.commit()
                    db.refresh(profile_data)
                    return ProfileData.model_validate(profile_data)
                except IntegrityError as e:
                    db.rollback()
                    raise ValueError(f"Failed to create profile data: {e}") from e

    def get_profile_data(self, profile_id: str) -> Optional[ProfileData]:
        """
        Get profile data by profile ID.

        Args:
            profile_id: ID of the profile to retrieve data for

        Returns:
            Optional[ProfileData]: Profile data object or None if not found
        """
        profile_id_uuid = (
            profile_id if isinstance(profile_id, UUID) else UUID(str(profile_id))
        )

        with get_session() as db:
            result = db.exec(
                select(TProfileData).where(TProfileData.profile_id == profile_id_uuid)
            )
            profile_data = result.one_or_none()
            return ProfileData.model_validate(profile_data) if profile_data else None

    def delete_profile_data(self, profile_id: str) -> bool:
        """
        Delete profile data for a profile.

        Args:
            profile_id: ID of the profile to delete data for

        Returns:
            bool: True if deleted, False if not found
        """
        profile_id_uuid = (
            profile_id if isinstance(profile_id, UUID) else UUID(str(profile_id))
        )

        with get_session() as db:
            result = db.exec(
                select(TProfileData).where(TProfileData.profile_id == profile_id_uuid)
            )
            profile_data = result.one_or_none()

            if profile_data:
                db.delete(profile_data)
                db.commit()
                return True
            return False
