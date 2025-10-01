"""
Database connection and session management for Luna.
Handles SQLModel engine setup, session lifecycle, and health checks.
"""

from typing import Optional

from sqlalchemy import Engine
from sqlmodel import Session, create_engine

from config.settings import AppSettings, get_settings

# Lazy initialization
_settings: Optional[AppSettings] = None
_engine: Optional[Engine] = None


def _get_settings() -> AppSettings:
    global _settings
    if _settings is None:
        _settings = get_settings()
    return _settings


def _get_engine() -> Engine:
    global _engine
    if _engine is None:
        settings = _get_settings()
        database_url = settings.database.get_connection_url()
        _engine = create_engine(
            database_url,
            pool_size=20,
            max_overflow=30,
            pool_pre_ping=True,
            pool_recycle=3600,
            echo=settings.logging.debug_mode,
        )
    return _engine


def get_session() -> Session:
    """
    Get a database session.
    Returns:
        Session: SQLModel session object.
    """
    return Session(_get_engine())


def db_health_check(retries: int = 3, delay: float = 1.0) -> bool:
    """
    Checks database connectivity with retries.
    Args:
        retries (int): Number of retry attempts.
        delay (float): Delay between retries in seconds.
    Returns:
        bool: True if DB is healthy, False otherwise.
    """
    # TODO: Implement database health check
    return True
