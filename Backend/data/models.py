"""
Data models for Luna using SQLModel.
Defines all database tables and relationships.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Column, Field, SQLModel


class ChannelType(str, Enum):
    TELEGRAM = "telegram"
    WHATSAPP = "whatsapp"
    PHONE = "phone"
    EMAIL = "email"
    SMS = "sms"


class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class HouseSign(str, Enum):
    ARIES = "aries"
    TAURUS = "taurus"
    GEMINI = "gemini"
    CANCER = "cancer"
    LEO = "leo"
    VIRGO = "virgo"
    LIBRA = "libra"
    SCORPIO = "scorpio"
    SAGITTARIUS = "sagittarius"
    CAPRICORN = "capricorn"
    AQUARIUS = "aquarius"
    PISCES = "pisces"


class RelationshipType(str, Enum):
    SELF = "self"
    PARENT = "parent"
    CHILD = "child"
    SIBLING = "sibling"
    FRIEND = "friend"
    PARTNER = "partner"
    OTHER = "other"


class NotificationType(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    WHATSAPP = "whatsapp"
    TELEGRAM = "telegram"
    PHONE = "phone"


class NotificationFrequency(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"


class MessageType(str, Enum):
    INCOMING_TEXT = "incoming-text"
    INCOMING_VOICE = "incoming-voice"
    OUTGOING_TEXT = "outgoing-text"
    OUTGOING_VOICE = "outgoing-voice"
    INCOMING_DOCUMENT = "incoming-document"
    OUTGOING_DOCUMENT = "outgoing-document"
    INCOMING_MEDIA = "incoming-media"
    OUTGOING_MEDIA = "outgoing-media"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    EXPIRED = "expired"


class ArtifactType(str, Enum):
    KUNDLI_PDF = "kundli_pdf"
    REPORT_IMAGE = "report_image"
    CHART_SVG = "chart_svg"
    OTHER = "other"


class TUser(SQLModel, table=True):
    """User table model."""

    __tablename__ = "users"

    user_id: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    phone: Optional[str]
    email: Optional[str]
    created_at: datetime
    updated_at: datetime


class TUserChannel(SQLModel, table=True):
    """User channel mapping table model."""

    __tablename__ = "user_channels"

    channel_id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.user_id")
    channel_type: ChannelType
    user_identity: str
    is_primary: bool = False
    created_at: datetime


class TLocations(SQLModel, table=True):
    """Locations table model."""

    __tablename__ = "locations"

    id: Optional[int] = Field(default=None, primary_key=True)
    source_id: Optional[int] = None
    city: str
    country: Optional[str] = None
    province: Optional[str] = None
    iso3: Optional[str] = None
    lat: float
    lng: float
    timezone: Optional[str] = None
    population: Optional[int] = None


class TCities(SQLModel, table=True):
    """Cities table model from pgAdmin database."""

    __tablename__ = "cities"

    id: Optional[int] = Field(default=None, primary_key=True)
    city: str = Field(index=True)  # City name with index for fast searching
    city_ascii: Optional[str] = None  # ASCII version of city name
    lat: Optional[float] = None  # Latitude
    lng: Optional[float] = None  # Longitude
    country: Optional[str] = None
    iso2: Optional[str] = None  # 2-character country code
    iso3: Optional[str] = None  # 3-character country code
    admin_name: Optional[str] = None  # State/region/province
    capital: Optional[str] = None  # Capital status
    population: Optional[float] = None  # Changed to float to match database


class TProfile(SQLModel, table=True):
    """Profile table model."""

    __tablename__ = "profiles"

    profile_id: UUID = Field(default_factory=uuid4, primary_key=True)
    birth_datetime: Optional[datetime]
    birth_place: Optional[str] = None
    birth_location_id: Optional[int] = Field(foreign_key="locations.id", default=None)
    name: Optional[str]
    gender: Optional[Gender]
    sun_sign: Optional[HouseSign]
    moon_sign: Optional[HouseSign]
    created_at: datetime
    updated_at: datetime


class TUserProfileLink(SQLModel, table=True):
    """User-profile relationship table model."""

    __tablename__ = "user_profile_links"

    profile_id: UUID = Field(
        foreign_key="profiles.profile_id", primary_key=True, index=True
    )
    user_id: UUID = Field(foreign_key="users.user_id", primary_key=True)
    relationship_type: RelationshipType
    created_at: datetime


class TProfileData(SQLModel, table=True):
    """Astrology data storage table model."""

    __tablename__ = "profile_data"

    profile_id: UUID = Field(
        foreign_key="profiles.profile_id", primary_key=True, index=True
    )
    kundli_data: Dict[str, Any] = Field(sa_column=Column(JSONB))
    horoscope_chart: Optional[Dict[str, Any]] = Field(sa_column=Column(JSONB))
    created_at: datetime
    updated_at: datetime


class TNotificationPreference(SQLModel, table=True):
    """Notification preferences table model."""

    __tablename__ = "notification_preferences"

    preference_id: UUID = Field(default_factory=uuid4, primary_key=True)
    profile_id: UUID = Field(foreign_key="profiles.profile_id", primary_key=True)
    notification_type: NotificationType
    frequency: NotificationFrequency
    channel: str
    enabled: bool = True
    created_at: datetime
    updated_at: datetime


class TConversation(SQLModel, table=True):
    """Conversation history table model."""

    __tablename__ = "conversations"

    message_id: Optional[int] = Field(default=None, primary_key=True)
    user_id: UUID = Field(foreign_key="users.user_id")
    channel: ChannelType
    message_type: MessageType
    content: str
    additional_info: Dict[str, Any] = Field(sa_column=Column(JSONB))
    created_at: datetime


class TSku(SQLModel, table=True):
    """SKU master table model."""

    __tablename__ = "skus"

    id: int = Field(primary_key=True)
    name: str
    sku_id: str = Field(unique=True)
    amount: float
    validity: int
    currency: str = Field(default="INR", max_length=3)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TUserPurchase(SQLModel, table=True):
    """User SKU purchases table model."""

    __tablename__ = "user_purchases"

    id: int = Field(primary_key=True, index=True)
    user_id: str = Field(index=True)
    payment_link_id: str
    status: PaymentStatus = Field(default=PaymentStatus.PENDING)
    sku_id: str = Field(foreign_key="skus.sku_id")
    valid_till: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TArtifact(SQLModel, table=True):
    __tablename__ = "artifacts"
    artifact_id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.user_id")
    filename: str
    s3_url: str
    artifact_type: ArtifactType
    content_type: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class TSKU(SQLModel, table=True):
    __tablename__ = "skus"
    __table_args__ = {"extend_existing": True}
    id: int = Field(primary_key=True)
    name: str
    sku_id: str = Field(unique=True, index=True)
    amount: float
    validity: int  # validity in days
    currency: str = Field(default="INR")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TUserPurchase(SQLModel, table=True):
    __tablename__ = "user_purchases"
    __table_args__ = {"extend_existing": True}
    id: int = Field(primary_key=True)
    user_id: str = Field(index=True)
    sku_id: str = Field(index=True)
    payment_link_id: str = Field(unique=True, index=True)
    status: str  # pending, paid, expired, failed
    valid_till: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
