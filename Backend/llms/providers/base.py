from abc import ABC, abstractmethod
from typing import List, Optional, Type

from pydantic import BaseModel

from config.settings import get_llm_settings

from ..models import LLMMessage, LLMProviders, LLMResponse


class Provider(ABC):
    def __init__(self):
        pass

    def get_provider_settings(self, provider: LLMProviders) -> dict:
        settings = get_llm_settings()
        provider_name: str = provider.value
        result = {}
        # Convention: <provider>_base_url, <provider>_api_key
        base_url = getattr(settings, f"provider_{provider_name}_base_url", None)
        api_key = getattr(settings, f"provider_{provider_name}_api_key", None)
        if base_url:
            result["base_url"] = base_url
        if api_key:
            result["api_key"] = api_key
        return result

    @abstractmethod
    async def get_response(
        self,
        model: str,
        messages: List[LLMMessage],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        response_model: Optional[Type[BaseModel]] = None,
    ) -> LLMResponse:
        """
        Generate a response from the LLM provider. If response_model is provided, attempts to return a structured object.
        Returns an LLMResponse with response_type ('text', 'object', or 'error'), text, object, error, and metadata.

        For debugging purposes, providers should include raw response data in metadata:
        - "raw_response": Provider-specific response object (e.g., OpenAI API response)
        - "raw_error": Provider-specific error details when exceptions occur
        - "usage": Token usage information when available
        """
        pass
