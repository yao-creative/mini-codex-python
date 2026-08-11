from abc import ABC, abstractmethod
from typing import Generic, TypeVar

RequestT = TypeVar("RequestT")
ResponseT = TypeVar("ResponseT")


class Adapter(ABC, Generic[RequestT, ResponseT]):
    """Port adapter: maps a domain request into an external response."""

    @abstractmethod
    async def execute(self, request: RequestT) -> ResponseT:
        ...