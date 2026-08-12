from abc import ABC, abstractmethod
from dataclasses import dataclass

import httpx

from adapters.base import Adapter
from monads import Err, Ok, Result, bind, catching


@dataclass(frozen=True)
class LLMRequest:
    model: str
    prompt: str


@dataclass(frozen=True)
class LLMResponse:
    text: str


@dataclass(frozen=True)
class LLMError:
    message: str


@dataclass(frozen=True)
class ModelUnavailable(LLMError):
    pass


@dataclass(frozen=True)
class ModelTimeout(LLMError):
    pass


@dataclass(frozen=True)
class InvalidLLMResponse(LLMError):
    pass


class LLMAadapter(Adapter[LLMRequest, LLMResponse], ABC):
    """Domain-level LLM adapter."""

    @abstractmethod
    @staticmethod
    async def complete(
        base_url: str,
        request: LLMRequest,
        client: httpx.AsyncClient = httpx.AsyncClient(),
    ) -> Result[LLMResponse, LLMError]: ...


class OllamaLLMAdapter(LLMAadapter):
    """Ollama HTTP adapter."""

    @staticmethod
    def complete(
        request: LLMRequest, client: httpx.AsyncClient = httpx.AsyncClient()
    ) -> Result[LLMResponse, LLMError]:

        response = catching(
            lambda: client.post(
                "/api/generate",
                json={"prompt": request.prompt},
            ),
            (
                httpx.TimeoutException,
                httpx.ConnectError,
            ),
            OllamaLLMAdapter.to_model_error,
        )
        return bind(response, OllamaLLMAdapter._parse_response)

    @staticmethod
    def _parse_response(
        response: httpx.Response,
    ) -> Result[LLMResponse, LLMError]:
        try:
            response.raise_for_status()
            data = response.json()
            return Ok(LLMResponse(data["response"]))

        except (httpx.HTTPError, ValueError, KeyError) as exc:
            return Err(InvalidLLMResponse(str(exc)))

    @staticmethod
    def to_model_error(exc: Exception) -> Result[LLMError]:
        if isinstance(exc, httpx.TimeoutException):
            return ModelTimeout("Ollama timed out")

        if isinstance(exc, httpx.ConnectError):
            return ModelUnavailable("Ollama unavailable")

        raise AssertionError(f"Unhandled exception: {exc!r}")
