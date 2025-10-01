"""
Logger utility for Luna using Loguru.
Handles structured logging, file rotation, and environment-based log levels.
Intercepts all Python logging and provides module-specific log levels.
"""

import json
import logging
import os
import sys
import uuid
from datetime import datetime
from typing import Any, Optional, Sequence, Tuple

from loguru import logger

from config.settings import LoggingSettings, get_log_settings

# Lazy initialization
_log_settings: Optional[LoggingSettings] = None
_logger_setup: bool = False


def _get_settings() -> LoggingSettings:
    global _log_settings
    if _log_settings is None:
        _log_settings = get_log_settings()
    return _log_settings




LOG_FILE = os.path.join("logs", "app.log")
os.makedirs("logs", exist_ok=True)

# Remove default handler
logger.remove()


# Patch logger to guarantee request_id and source location are always set
def patch_logger(record):
    # Ensure message newlines are escaped to keep logs single-line per entry
    if isinstance(record.get("message"), str):
        record["message"] = record["message"].replace("\n", "\\n")
    record["extra"].setdefault("request_id", "-")
    # For direct loguru calls, use the current frame info
    if "source_name" not in record["extra"]:
        import inspect

        # Walk up the call stack to find the actual caller (skip loguru internals, our patch function, and our logging wrappers)
        frame = inspect.currentframe()
        while frame and (
            "loguru" in frame.f_code.co_filename
            or frame.f_code.co_name
            in [
                "_log",
                "log",
                "info",
                "debug",
                "warning",
                "error",
                "critical",
                "patch_logger",
                "_bind_llm_logger",
                "log_llm_request",
                "log_llm_response",
            ]
        ):
            frame = frame.f_back

        if frame:
            record["extra"]["source_name"] = frame.f_globals.get("__name__", "unknown")
            record["extra"]["source_function"] = frame.f_code.co_name
            record["extra"]["source_line"] = frame.f_lineno


logger = logger.patch(patch_logger)


class InterceptHandler(logging.Handler):
    """
    Intercepts standard Python logging and routes it through Loguru.
    This ensures all logs (including SQLModel/SQLAlchemy) go through our custom logger.
    """

    def emit(self, record: logging.LogRecord) -> None:
        # Get corresponding Loguru level
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Bind the original record's location information
        loguru_record = logger.bind(
            request_id="-",
            source_name=record.name,
            source_function=record.funcName,
            source_line=record.lineno,
        )
        loguru_record.opt(exception=record.exc_info).log(level, record.getMessage())


def _setup_logger():
    """Setup logger handlers with settings and intercept standard logging."""
    global _logger_setup
    if _logger_setup:
        return

    settings = _get_settings()

    # Add stdout handler for LLM events
    logger.add(
        sys.stdout,
        format="{time:YYYY-MM-DD HH:mm:ss.SSSZZ} | LLM      | {extra[source_name]}:{extra[source_function]}:{extra[source_line]} | {extra[request_id]} | {message}",
        level=settings.default_log_level,
        enqueue=True,
        backtrace=True,
        diagnose=settings.debug_mode,
        colorize=False,
        filter=lambda record: record["extra"].get("llm_event") is True,
    )
    
    # Add stdout handler for access logs
    logger.add(
        sys.stdout,
        format="{time:YYYY-MM-DD HH:mm:ss.SSSZZ} | ACCESS   | {extra[source_name]}:{extra[source_function]}:{extra[source_line]} | {extra[request_id]} | {message}",
        level=settings.default_log_level,
        enqueue=True,
        backtrace=True,
        diagnose=settings.debug_mode,
        colorize=False,
        filter=lambda record: record["extra"].get("access_log") is True,
    )
    
    # Add stdout handler for general logs
    logger.add(
        sys.stdout,
        format="{time:YYYY-MM-DD HH:mm:ss.SSSZZ} | {level: <8} | {extra[source_name]}:{extra[source_function]}:{extra[source_line]} | {extra[request_id]} | {message}",
        level=settings.default_log_level,
        enqueue=True,
        backtrace=True,
        diagnose=settings.debug_mode,
        colorize=False,
        filter=lambda record: record["extra"].get("llm_event") is not True and record["extra"].get("access_log") is not True,
    )



    # Add file handler for LLM events
    logger.add(
        LOG_FILE,
        format="{time:YYYY-MM-DD HH:mm:ss.SSSZZ} | LLM      | {extra[source_name]}:{extra[source_function]}:{extra[source_line]} | {extra[request_id]} | {message}",
        level=settings.default_log_level,
        rotation="10 MB",
        retention="30 days",
        compression="zip",
        enqueue=True,
        backtrace=True,
        diagnose=settings.debug_mode,
        filter=lambda record: record["extra"].get("llm_event") is True,
    )
    
    # Add file handler for access logs
    logger.add(
        LOG_FILE,
        format="{time:YYYY-MM-DD HH:mm:ss.SSSZZ} | ACCESS   | {extra[source_name]}:{extra[source_function]}:{extra[source_line]} | {extra[request_id]} | {message}",
        level=settings.default_log_level,
        rotation="10 MB",
        retention="30 days",
        compression="zip",
        enqueue=True,
        backtrace=True,
        diagnose=settings.debug_mode,
        filter=lambda record: record["extra"].get("access_log") is True,
    )
    
    # Add file handler for general logs
    logger.add(
        LOG_FILE,
        format="{time:YYYY-MM-DD HH:mm:ss.SSSZZ} | {level: <8} | {extra[source_name]}:{extra[source_function]}:{extra[source_line]} | {extra[request_id]} | {message}",
        level=settings.default_log_level,
        rotation="10 MB",
        retention="30 days",
        compression="zip",
        enqueue=True,
        backtrace=True,
        diagnose=settings.debug_mode,
        filter=lambda record: record["extra"].get("llm_event") is not True and record["extra"].get("access_log") is not True,
    )

    # Intercept all standard Python logging
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    # Configure module-specific log levels from settings (only for configured modules)
    settings = _get_settings()

    # Configure SQLAlchemy engine logging
    if settings.sqlalchemy_engine_level:
        logging.getLogger("sqlalchemy.engine").setLevel(
            getattr(logging, settings.sqlalchemy_engine_level)
        )

    _logger_setup = True


def configure_module_log_level(module_name: str, level: str) -> None:
    """
    Configure log level for a specific module at runtime.

    Args:
        module_name (str): Name of the module (e.g., 'sqlalchemy.engine', 'openai')
        level (str): Log level ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
    """
    if level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
        raise ValueError(f"Invalid log level: {level}")

    logging.getLogger(module_name).setLevel(getattr(logging, level))


def get_logger(request_id: str = "-"):
    """
    Returns a logger instance with request_id bound for tracing.
    Args:
        request_id (str): Correlation/request ID for tracing.
    Returns:
        loguru.Logger: Logger instance with context.
    """
    _setup_logger()  # Setup logger when first accessed
    return logger.bind(request_id=request_id)


# LLM Event Logging Functions
def generate_request_id() -> str:
    """Generate a unique request ID for LLM operations."""
    return str(uuid.uuid4())


def _bind_llm_logger(function_name: str, request_id: str):
    """Bind required extras for LLM event logging."""
    return logger.bind(
        llm_event=True,
        request_id=request_id,
        # Remove hardcoded source information - let patch_logger detect it automatically
        # source_name="llms.event_logger",
        # source_function=function_name,
        # source_line=0,
    )


def log_llm_request(
    *,
    request_id: str,
    messages: Sequence[Any],
    max_tokens: Optional[int],
    temperature: Optional[float],
    auto: bool,
    preferred_models: Optional[Sequence[Tuple[Any, Any]]],
    response_model: Optional[str],
) -> None:
    """Log LLM request details."""
    event = {
        "request_id": request_id,
        "time": datetime.now().astimezone().isoformat(),
        "request": {
            "messages": [
                {"role": m.role.value, "content": m.content} for m in messages
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "auto": auto,
            "preferred_models": [
                (getattr(p, "value", str(p)), getattr(m, "value", str(m)))
                for p, m in (preferred_models or [])
            ],
            "response_model": response_model,
        },
    }
    _bind_llm_logger("log_llm_request", request_id).info(json.dumps(event))


def log_llm_response(*, request_id: str, response: Any) -> None:
    """Log LLM response details."""
    try:
        # Simply log the response object's JSON form
        # The event logger shouldn't care about the internal structure
        event = {
            "request_id": request_id,
            "time": datetime.now().astimezone().isoformat(),
            "response": json.loads(
                response.model_dump_json()
            ),  # to deal with date and time serialization issues
        }
        _bind_llm_logger("log_llm_response", request_id).info(json.dumps(event))

    except Exception as e:
        # If anything goes wrong with logging, log a minimal event and the error
        # This ensures logging never causes the main functionality to fail
        error_event = {
            "request_id": request_id,
            "time": datetime.now().astimezone().isoformat(),
            "error_message": "Failed to log LLM response details",
            "logging_error": str(e),
            "response_type": getattr(response, "response_type", "unknown"),
            "has_error": response.error is not None,
        }
        _bind_llm_logger("log_llm_response", request_id).warning(
            json.dumps(error_event)
        )
