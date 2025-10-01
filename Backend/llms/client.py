from typing import List, Optional, Tuple, Type

from pydantic import BaseModel

from config.settings import get_llm_settings
from llms.providers.openai import OpenAIProvider
from utils.logger import (
    generate_request_id,
    get_logger,
    log_llm_request,
    log_llm_response,
)

from .models import (
    LLMError,
    LLMMessage,
    LLMModels,
    LLMProviders,
    LLMResponse,
    LLMResponseMetadata,
    LLMResponseType,
)
from .providers.base import Provider


class LLMClientError(Exception):
    """Exception raised for errors related to LLM provider/model selection."""

    pass


class LLMClient:
    def __init__(self):
        try:
            self.config = get_llm_settings()
            self.providers: dict[LLMProviders, Provider] = {}
            
            # Only initialize providers that have valid configuration
            if self.config.provider_openai_api_key:
                try:
                    self.providers[LLMProviders.OPENAI] = OpenAIProvider()
                except Exception as e:
                    self.logger = get_logger()
                    self.logger.warning(f"⚠️ Failed to initialize OpenAI provider: {e}")
            
            self.logger = get_logger()
            
            if not self.providers:
                self.logger.warning("⚠️ No LLM providers initialized - LLM functionality will not be available")
                
        except Exception as e:
            # Fallback initialization if settings fail
            self.config = None
            self.providers = {}
            try:
                self.logger = get_logger()
                self.logger.warning(f"Failed to initialize LLM client: {e}")
            except Exception as e:
                # Last resort - no logging available
                pass

    async def get_response(
        self,
        messages: List[LLMMessage],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = 0.5,
        auto: bool = True,
        preferred_models: Optional[List[Tuple[LLMProviders, LLMModels]]] = None,
        response_model: Optional[Type[BaseModel]] = None,
    ) -> LLMResponse:
        """
        Generate a response using the best available provider/model.

        Parameters:
            messages (List[LLMMessage]):
                The conversation history as a list of LLMMessage objects, typically including user and system messages.
            max_tokens (Optional[int]):
                The maximum number of tokens to generate in the response. If None, the provider/model default is used.
            temperature (Optional[float]):
                Sampling temperature for response randomness. Higher values (e.g., 0.8) make output more random, lower values (e.g., 0.2) make it more deterministic. Defaults to 0.5.
            auto (bool):
                If True, use the default or allowed providers/models from settings when preferred_models is not specified or not allowed. If False, preferred_models must be provided and only those will be tried.
            preferred_models (Optional[List[Tuple[LLMProviders, LLMModels]]]):
                An ordered list of (provider, model) tuples to try, in preference order. Only those allowed by config will be used. If None, auto/default selection is used.
            response_model (Optional[Type[BaseModel]]):
                If provided, the response will be parsed and returned as an instance of this Pydantic model. If None, a plain text response is returned.

        Returns:
            LLMResponse: The response object containing the generated text, structured object, or error details.

        Raises:
            LLMClientError: If no usable models are found in preferred_models and auto is False, or if neither auto is True nor preferred_models is specified. This typically indicates a configuration or usage error where no valid provider/model combination is available for generating a response.
        """
        if not self.config:
            raise LLMClientError("LLM client not properly configured - no settings available")
            
        allowed_providers = set(self.config.allowed_providers)
        allowed_models = set(self.config.allowed_models)
        default_provider = LLMProviders(self.config.default_provider)
        default_model = LLMModels(self.config.default_model)

        # Build candidate list
        candidates = []
        if preferred_models:
            # Only keep those in allowed config
            for prov, mod in preferred_models:
                if prov.value in allowed_providers and mod.value in allowed_models:
                    candidates.append((prov, mod))
            if not candidates:
                if auto:
                    candidates = [(default_provider, default_model)]
                else:
                    raise LLMClientError(
                        "No usable models in preferred_models and auto is False."
                    )
        elif auto:
            candidates = [(default_provider, default_model)]
        else:
            raise LLMClientError("Must specify either auto=True or preferred_models.")

        # Assign a request_id and log the request event
        request_id = generate_request_id()
        try:
            log_llm_request(
                request_id=request_id,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                auto=auto,
                preferred_models=candidates,
                response_model=(response_model.__name__ if response_model else None),
            )
        except Exception as e:
            # Log the logging failure but don't let it affect the main functionality
            self.logger.warning(
                f"Failed to log LLM request for request {request_id}: {e}"
            )

        last_error = None
        tried = []
        for provider, model in candidates:
            if provider not in self.providers:
                tried.append(
                    (provider, model, "Provider not available in self.providers")
                )
                continue
            try:
                if response_model is not None:
                    llm_response = await self.providers[provider].get_response(
                        model.value,
                        messages,
                        max_tokens,
                        temperature,
                        response_model,
                    )
                else:
                    llm_response = await self.providers[provider].get_response(
                        model=model.value,
                        messages=messages,
                        max_tokens=max_tokens,
                        temperature=temperature,
                    )
                # Ensure request_id present in metadata
                try:
                    if llm_response.metadata is None:
                        llm_response.metadata = LLMResponseMetadata()
                    llm_response.metadata.request_id = request_id
                except Exception:
                    pass

                # Log the response safely - ensure logging never fails
                try:
                    log_llm_response(request_id=request_id, response=llm_response)
                except Exception as e:
                    # Log the logging failure but don't let it affect the main functionality
                    self.logger.warning(
                        f"Failed to log LLM response for request {request_id}: {e}"
                    )

                return llm_response
            except Exception as e:
                last_error = e
                tried.append((provider, model, str(e)))
                error_response = LLMResponse(
                    response_type=LLMResponseType.ERROR,
                    text=None,
                    object=None,
                    error=LLMError(type="exception", message=str(e)),
                    metadata=LLMResponseMetadata(request_id=request_id),
                )
                # Log the error response safely - ensure logging never fails
                try:
                    log_llm_response(request_id=request_id, response=error_response)
                except Exception as log_e:
                    # Log the logging failure but don't let it affect the main functionality
                    self.logger.warning(
                        f"Failed to log LLM error response for request {request_id}: {log_e}"
                    )
                continue
        final_error_response = LLMResponse(
            response_type=LLMResponseType.ERROR,
            text=None,
            object=None,
            error=LLMError(type="provider_error", message=str(last_error)),
            metadata=LLMResponseMetadata(request_id=request_id),
        )

        # Log the final error response safely - ensure logging never fails
        try:
            log_llm_response(request_id=request_id, response=final_error_response)
        except Exception as log_e:
            # Log the logging failure but don't let it affect the main functionality
            self.logger.warning(
                f"Failed to log final LLM error response for request {request_id}: {log_e}"
            )

        return final_error_response
