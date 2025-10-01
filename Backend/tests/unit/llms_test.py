import asyncio

from pydantic import BaseModel

from llms.client import LLMClient
from llms.models import LLMMessage, LLMMessageRole, LLMResponse


class UserResponse(BaseModel):
    name: str
    age: int


def test_text_generation():
    """Test basic text generation with LLM client."""

    async def _test():
        client = LLMClient()
        messages = [
            LLMMessage(
                role=LLMMessageRole.SYSTEM, content="You are a helpful assistant."
            ),
            LLMMessage(
                role=LLMMessageRole.USER,
                content="Provide a random user info with name and age.",
            ),
        ]
        response = await client.get_response(
            messages=messages,
            max_tokens=50,
            temperature=0.7,
        )

        # Assert that we got a response
        assert response is not None
        assert hasattr(response, "text")
        assert isinstance(response.text, str)
        assert len(response.text) > 0
        print(f"Text generation response: {response.text}")

    asyncio.run(_test())


def test_structured_generation():
    """Test structured generation with LLM client."""

    async def _test():
        client = LLMClient()
        messages = [
            LLMMessage(
                role=LLMMessageRole.SYSTEM, content="You are a helpful assistant."
            ),
            LLMMessage(
                role=LLMMessageRole.USER,
                content="Provide a random user info with name and age.",
            ),
        ]

        structured_response = await client.get_response(
            messages=messages,
            response_model=UserResponse,
        )

        # Assert that we got a structured response of type OBJECT and the embedded object has name and age
        assert structured_response is not None
        assert isinstance(structured_response, LLMResponse)
        obj = getattr(structured_response, "object", None)
        assert obj is not None
        assert hasattr(obj, "name")
        assert hasattr(obj, "age")
        assert isinstance(obj.name, str)
        assert isinstance(obj.age, int)
        assert len(obj.name) > 0
        assert obj.age > 0
        print(f"Structured response object: {obj}")

    asyncio.run(_test())
