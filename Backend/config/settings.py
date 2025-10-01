"""
Configuration management for Luna using Pydantic BaseSettings.
Loads environment variables, supports nested config, and provides a cached settings instance.
"""

import json
import os
import time
from threading import RLock
from typing import Optional

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()

# Cache settings with timeout (1 hour = 3600 seconds)
CACHE_TIMEOUT_SECONDS = 3600
_settings_cache: Optional["AppSettings"] = None
_cache_timestamp: float = 0.0
_cache_lock = RLock()  # RLock allows recursive acquisition


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""

    url: Optional[str] = Field(
        default=None,
        description="Database connection URL (e.g., postgresql://user:pass@host:port/db)"
    )

    model_config = SettingsConfigDict(env_prefix="DB_", extra="ignore")
    
    def get_connection_url(self) -> Optional[str]:
        """Get the database connection URL"""
        return self.url
    
    def is_configured(self) -> bool:
        """Check if database is properly configured"""
        return self.url is not None and self.url.strip() != ""


class TelegramSettings(BaseSettings):
    """Telegram channel configuration settings."""

    bot_token: Optional[str] = ""
    webhook_secret: Optional[str] = ""  # Secret for webhook verification
    max_message_length: int = 4096  # Telegram message length limit
    webhook_base_url: Optional[str] = ""
    webhook_path: str = "/webhook/telegram"  # Configurable webhook path

    model_config = SettingsConfigDict(env_prefix="TELEGRAM_", extra="ignore")


class WhatsAppSettings(BaseSettings):
    """WhatsApp channel configuration settings."""

    access_token: Optional[str] = ""  # WhatsApp Business API access token
    phone_number_id: Optional[str] = ""  # WhatsApp phone number ID
    webhook_verify_token: Optional[str] = ""  # Webhook verification token
    webhook_secret: Optional[str] = ""  # Secret for webhook verification
    max_message_length: int = 4096  # WhatsApp message length limit
    webhook_path: str = "/webhook/whatsapp"  # Configurable webhook path

    model_config = SettingsConfigDict(env_prefix="WHATSAPP_", extra="ignore")


class APISettings(BaseSettings):
    """API keys for external providers."""

    divine_api_key: Optional[str] = ""
    divine_access_token: Optional[str] = ""
    elevenlabs_api_key: Optional[str] = ""
    sarvam_api_key: Optional[str] = ""

    model_config = SettingsConfigDict(env_prefix="", extra="ignore")


class AWSSettings(BaseSettings):
    """AWS configuration settings."""

    access_key_id: Optional[str] = ""
    secret_access_key: Optional[str] = ""
    s3_bucket_name: Optional[str] = ""
    region: str = "ap-south-1"

    model_config = SettingsConfigDict(env_prefix="AWS_", extra="ignore")


class LLMSettings(BaseSettings):
    """LLM provider and model configuration settings."""

    allowed_providers: list[str] = []
    allowed_models: list[str] = []
    default_provider: str = "openai"
    default_model: str = "gpt-4.1-mini"

    # Example for OpenAI, Google, etc. Add more as needed.
    provider_openai_base_url: Optional[str] = "https://api.openai.com/v1"
    provider_openai_api_key: Optional[str] = ""
    provider_google_base_url: Optional[str] = ""
    provider_google_api_key: Optional[str] = ""
    # Add more providers as needed

    model_config = SettingsConfigDict(env_prefix="LLM_", extra="ignore")


class SessionSettings(BaseSettings):
    """Settings for session management."""

    max_turns_in_cache: int = 20
    max_cache_size: int = 10000  # Max size in characters

    model_config = SettingsConfigDict(env_prefix="SESSION_", extra="ignore")


class LoggingSettings(BaseSettings):
    """Settings for logging configuration."""

    debug_mode: bool = True
    default_log_level: str = "INFO"

    # Optional module-specific log levels (only set when needed)
    sqlalchemy_engine_level: Optional[str] = None  # For SQLAlchemy engine logs

    model_config = SettingsConfigDict(env_prefix="LOG_", extra="ignore")


class GeolocationSettings(BaseSettings):
    """Geolocation service configuration settings."""

    enabled: bool = True
    fuzzy_matching_enabled: bool = True
    fuzzy_match_threshold: float = 0.6
    max_candidates: int = 5

    model_config = SettingsConfigDict(env_prefix="GEOLOC_", extra="ignore")


class RazorpaySettings(BaseSettings):
    """Razorpay payment gateway settings."""

    API_KEY: Optional[str] = ""
    API_SECRET: Optional[str] = ""
    BASE_URL: str = "https://api.razorpay.com/v1"
    CALLBACK_BASE_URL: Optional[str] = ""

    model_config = SettingsConfigDict(env_prefix="RAZORPAY_", extra="ignore")


class SchedulingSettings(BaseSettings):
    """Background task scheduling configuration settings."""

    # Payment status polling frequency (in seconds)
    payment_polling_interval: int = 60  # Default: every 60 seconds

    # Subscription expiry check frequency (in seconds)
    subscription_check_interval: int = 86400  # Default: every 24 hours (24 * 60 * 60)

    # Enable/disable background tasks
    enable_payment_polling: bool = True
    enable_subscription_checks: bool = True

    model_config = SettingsConfigDict(env_prefix="SCHEDULING_", extra="ignore")


class KundliSettings(BaseSettings):
    """Kundli generation configuration settings."""

    # Enable/disable sending PDF files to users
    send_pdf_to_user: bool = False

    model_config = SettingsConfigDict(env_prefix="KUNDLI_", extra="ignore")


class AppSettings(BaseSettings):
    """Application-wide configuration settings."""

    database: DatabaseSettings = Field(default_factory=lambda: DatabaseSettings())
    telegram: TelegramSettings = Field(default_factory=lambda: TelegramSettings())
    whatsapp: WhatsAppSettings = Field(default_factory=lambda: WhatsAppSettings())
    apis: APISettings = Field(default_factory=lambda: APISettings())
    aws: AWSSettings = Field(default_factory=lambda: AWSSettings())
    llm: LLMSettings = Field(default_factory=lambda: LLMSettings())
    session: SessionSettings = Field(default_factory=lambda: SessionSettings())
    logging: LoggingSettings = Field(default_factory=lambda: LoggingSettings())
    geolocation: GeolocationSettings = Field(default_factory=lambda: GeolocationSettings())
    razorpay: RazorpaySettings = Field(default_factory=lambda: RazorpaySettings())
    scheduling: SchedulingSettings = Field(default_factory=lambda: SchedulingSettings())
    kundli: KundliSettings = Field(default_factory=lambda: KundliSettings())

    model_config = SettingsConfigDict(env_prefix="", extra="ignore")
    
    def __init__(self, **kwargs):
        """Initialize AppSettings from JSON config or fallback to individual settings classes."""
        config_json = os.getenv("LUNA_CONFIG_JSON")
        
        if config_json:
            # Load from JSON
            try:
                config_dict = json.loads(config_json)
                
                # Create nested settings objects from dict sections
                settings_classes = {
                    "database": DatabaseSettings,
                    "telegram": TelegramSettings,
                    "whatsapp": WhatsAppSettings,
                    "apis": APISettings,
                    "aws": AWSSettings,
                    "llm": LLMSettings,
                    "session": SessionSettings,
                    "logging": LoggingSettings,
                    "geolocation": GeolocationSettings,
                    "razorpay": RazorpaySettings,
                    "scheduling": SchedulingSettings,
                    "kundli": KundliSettings,
                }
                
                for section_name, settings_class in settings_classes.items():
                    if section_name in config_dict:
                        kwargs[section_name] = settings_class(**config_dict[section_name])
                
            except (json.JSONDecodeError, KeyError, TypeError) as e:
                raise ValueError(f"Invalid LUNA_CONFIG_JSON: {e}")
        
        # Initialize with kwargs (either from JSON or default factories)
        super().__init__(**kwargs)
    
    def is_minimal_config(self) -> bool:
        """Check if app is running with minimal configuration (missing critical settings)"""
        return not self.database.is_configured()


def get_settings() -> AppSettings:
    """
    Returns a cached AppSettings instance.
    Loads from LUNA_CONFIG_JSON if available, otherwise from environment variables.
    Settings are cached for 1 hour, after which a fresh instance is created.

    Returns:
        AppSettings: The application settings object.
    """
    global _settings_cache, _cache_timestamp

    # Fast path: check cache validity without lock first
    current_time = time.time()
    if _settings_cache is not None and (current_time - _cache_timestamp) < CACHE_TIMEOUT_SECONDS:
        return _settings_cache

    # Slow path: acquire lock and double-check (another thread might have updated cache)
    with _cache_lock:
        # Double-check pattern to avoid race conditions
        current_time = time.time()  # Re-check time under lock
        if _settings_cache is not None and (current_time - _cache_timestamp) < CACHE_TIMEOUT_SECONDS:
            return _settings_cache

        # Cache is stale or doesn't exist, create new settings
        _settings_cache = AppSettings()
        _cache_timestamp = current_time
        return _settings_cache


def clear_settings_cache() -> None:
    """
    Manually clears the settings cache. Useful for testing or forcing a refresh.
    """
    global _settings_cache, _cache_timestamp

    with _cache_lock:
        _settings_cache = None
        _cache_timestamp = 0.0


def get_llm_settings() -> LLMSettings:
    """
    Returns a cached LLMSettings instance loaded from environment variables and .env file.
    Returns:
        LLMSettings: The LLM settings object.
    """
    return get_settings().llm


def get_session_settings() -> SessionSettings:
    """
    Returns a cached SessionSettings instance loaded from environment variables and .env file.
    Returns:
        SessionSettings: The Session settings object.
    """
    return get_settings().session


def get_log_settings() -> LoggingSettings:
    """
    Returns a cached LoggingSettings instance loaded from environment variables and .env file.
    Returns:
        LoggingSettings: The Session settings object.
    """
    return get_settings().logging


def get_geolocation_settings() -> GeolocationSettings:
    """
    Returns a cached GeolocationSettings instance loaded from environment variables and .env file.
    Returns:
        GeolocationSettings: The Geolocation settings object.
    """
    return get_settings().geolocation


def get_scheduling_settings() -> SchedulingSettings:
    """
    Returns a cached SchedulingSettings instance loaded from environment variables and .env file.
    Returns:
        SchedulingSettings: The scheduling settings object.
    """
    return get_settings().scheduling


def get_razorpay_settings() -> RazorpaySettings:
    """
    Returns a cached RazorpaySettings instance loaded from environment variables and .env file.
    Returns:
        RazorpaySettings: The Razorpay settings object.
    """
    return get_settings().razorpay


def get_kundli_settings() -> KundliSettings:
    """
    Returns a cached KundliSettings instance loaded from environment variables and .env file.
    Returns:
        KundliSettings: The kundli settings object.
    """
    return get_settings().kundli
