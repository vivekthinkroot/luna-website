from typing import Any, List, Optional, Type

import openai
from openai.types.responses import (
    EasyInputMessageParam,
    ResponseInputItemParam,
)
from pydantic import BaseModel

from utils.logger import get_logger

from ..models import (
    LLMError,
    LLMMessage,
    LLMProviders,
    LLMResponse,
    LLMResponseMetadata,
    LLMResponseType,
    OpenAIRawResponse,
)
from .base import Provider

logger = get_logger()


class OpenAIProvider(Provider):
    def __init__(self):
        super().__init__()
        provider_settings = self.get_provider_settings(LLMProviders.OPENAI)
        self.base_url = provider_settings.get("base_url")
        self.api_key = provider_settings.get("api_key")
        self._client = openai.AsyncOpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
        )

    def safe_string(self, obj: Any) -> str:
        try:
            return str(obj)
        except Exception:
            try:
                return repr(obj)
            except Exception:
                return f"<unstringifiable object of type {type(obj).__name__}>"


    def _create_raw_response_metadata(
        self,
        openai_response,
        response_text: Optional[str] = None,
        response_object: Optional[Any] = None,
        response_model_name: Optional[str] = None,
    ) -> OpenAIRawResponse:
        """Create structured metadata from OpenAI response."""
        try:
            # Extract basic response info
            raw_data = openai_response.model_dump()

            # Check for errors
            has_error = openai_response.error is not None
            error_message = openai_response.error.message if has_error else None

            # Check for usage info
            has_usage = (
                hasattr(openai_response, "usage") and openai_response.usage is not None
            )
            usage_tokens = None
            if has_usage:
                usage_data = (
                    openai_response.usage.model_dump()
                    if hasattr(openai_response.usage, "model_dump")
                    else openai_response.usage
                )
                usage_tokens = {
                    "input_tokens": usage_data.get("input_tokens"),
                    "output_tokens": usage_data.get("output_tokens"),
                    "total_tokens": usage_data.get("total_tokens"),
                }

            return OpenAIRawResponse(
                id=raw_data.get("id"),
                model=raw_data.get("model"),
                created=raw_data.get("created"),
                object=raw_data.get("object"),
                has_error=has_error,
                has_usage=has_usage,
                error_message=error_message,
                usage_tokens=usage_tokens,
                raw_data_type="OpenAIResponse",
                response_text=response_text,
                response_object=response_object,
                response_model_name=response_model_name,
            )
        except Exception as e:
            logger.warning(f"Failed to create structured raw response metadata: {e}")
            return OpenAIRawResponse(
                has_error=True,
                error_message=f"Failed to parse response metadata: {str(e)}",
                raw_data_type="OpenAIResponse",
                response_text=response_text,
                response_object=response_object,
                response_model_name=response_model_name,
            )

    async def get_response(
        self,
        model: str,
        messages: List[LLMMessage],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = 0.5,
        response_model: Optional[Type[BaseModel]] = None,
    ) -> LLMResponse:
        openai_response = None
        openai_response_text = None
        openai_response_model = None

        try:
            openai_messages: List[ResponseInputItemParam] = [
                EasyInputMessageParam(role=msg.role.value, content=msg.content)
                for msg in messages
            ]

            if response_model is None:
                openai_response = await self._client.responses.create(
                    model=model,
                    input=openai_messages,
                    max_output_tokens=max_tokens,
                    temperature=temperature,
                    store=False,
                )
                openai_response_text = openai_response.output_text
            else:
                openai_response = await self._client.responses.parse(
                    model=model,
                    input=openai_messages,
                    max_output_tokens=max_tokens,
                    temperature=temperature,
                    text_format=response_model,
                    store=False,
                )
                openai_response_model = openai_response.output_parsed

            # Create structured metadata
            raw_response_metadata = self._create_raw_response_metadata(
                openai_response,
                response_text=openai_response_text if response_model is None else None,
                response_object=(
                    openai_response_model if response_model is not None else None
                ),
                response_model_name=(
                    response_model.__name__ if response_model is not None else None
                ),
            )

            if openai_response.error is not None:
                logger.error(f"OpenAI error: {openai_response.error}")
                return LLMResponse(
                    response_type=LLMResponseType.ERROR,
                    text=None,
                    object=None,
                    error=LLMError(
                        type="openai_error", message=openai_response.error.message
                    ),
                    metadata=LLMResponseMetadata(raw_response=raw_response_metadata),
                )
            else:
                if response_model is not None:
                    return LLMResponse(
                        response_type=LLMResponseType.OBJECT,
                        text=None,
                        object=openai_response_model,
                        error=None,
                        metadata=LLMResponseMetadata(
                            usage=(
                                openai_response.usage.model_dump()
                                if openai_response.usage
                                and hasattr(openai_response.usage, "model_dump")
                                else openai_response.usage
                            ),
                            raw_response=raw_response_metadata,
                        ),
                    )
                else:
                    return LLMResponse(
                        response_type=LLMResponseType.TEXT,
                        text=openai_response_text,
                        object=None,
                        error=None,
                        metadata=LLMResponseMetadata(
                            usage=(
                                openai_response.usage.model_dump()
                                if openai_response.usage
                                and hasattr(openai_response.usage, "model_dump")
                                else openai_response.usage
                            ),
                            raw_response=raw_response_metadata,
                        ),
                    )
        except Exception as e:
            logger.error(f"OpenAI Exception: {str(e)}, with raw response: {self.safe_string(openai_response)}")

            # Create raw response metadata if we have a response object
            raw_response_metadata = None
            if openai_response is not None:
                raw_response_metadata = self._create_raw_response_metadata(
                    openai_response,
                    response_text=openai_response_text,
                    response_object=openai_response_model,
                    response_model_name=(
                        response_model.__name__ if response_model is not None else None
                    ),
                )

            return LLMResponse(
                response_type=LLMResponseType.ERROR,
                text=None,
                object=None,
                error=LLMError(type="openai_exception", message=str(e)),
                metadata=LLMResponseMetadata(
                    raw_response=raw_response_metadata,
                    raw_error={
                        "exception_type": type(e).__name__,
                        "exception_message": str(e),
                    },
                ),
            )
