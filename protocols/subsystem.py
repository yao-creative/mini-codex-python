from typing import Protocol
from events.base import Event
from states.base import BaseState
from result import Result

class Subsystem(Protocol):
    @staticmethod
    def owns(event: Event) -> bool: ...
    @staticmethod
    def apply(state: BaseState, event: Event) -> Result[BaseState, object]: ...  # projects its OWN domain internally
