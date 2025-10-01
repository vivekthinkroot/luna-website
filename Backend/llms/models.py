from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel


class LLMProviders(str, Enum):
    OPENAI = "openai"


class LLMModels(str, Enum):
    GPT_4_1_NANO = "gpt-4.1-nano"
    GPT_4_1_MINI = "gpt-4.1-mini"
    O4_MINI = "o4-mini"


class LLMMessageRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class LLMMessage(BaseModel):
    role: LLMMessageRole
    content: str


class LLMError(BaseModel):
    type: str
    message: str
    details: Optional[Dict[str, Any]] = None


class LLMResponseType(str, Enum):
    TEXT = "text"
    OBJECT = "object"
    ERROR = "error"


class OpenAIRawResponse(BaseModel):
    """Structured representation of OpenAI API response metadata."""

    id: Optional[str] = None
    model: Optional[str] = None
    created: Optional[int] = None
    object: Optional[str] = None
    has_error: bool = False
    has_usage: bool = False
    error_message: Optional[str] = None
    usage_tokens: Optional[Dict[str, int]] = None
    raw_data_type: str = "OpenAIResponse"
    # Response content fields
    response_text: Optional[str] = None
    response_object: Optional[Any] = None
    response_model_name: Optional[str] = None


class LLMResponseMetadata(BaseModel):
    """Structured metadata for LLM responses."""

    request_id: Optional[str] = None
    raw_response: Optional[OpenAIRawResponse] = None
    raw_error: Optional[Dict[str, Any]] = None
    usage: Optional[Any] = (
        None  # Flexible type to handle different provider response types
    )


class LLMResponse(BaseModel):
    response_type: LLMResponseType
    text: Optional[str] = None
    object: Optional[Any] = None
    error: Optional[LLMError] = None
    metadata: LLMResponseMetadata = LLMResponseMetadata()
