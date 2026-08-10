from events.base import Event
from dataclasses import dataclass


@dataclass(frozen=True)
class AgentEvent(Event):
    """E_cmd — abstract base; never constructed directly, only its variants below."""

