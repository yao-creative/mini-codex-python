from events.base import Event
from dataclasses import dataclass


@dataclass(frozen=True)
class AgentEvent(Event):
    """E_cmd — abstract base; never constructed directly, only its variants below."""


@dataclass(frozen=True)
class Start(AgentEvent):
    request_id: str

@dataclass(frozen=True)
class CompletionReceived(AgentEvent):
    request_id: str | None
    tool_call_id: str | None

    def __post_init__(self) -> None:
        if (self.request_id is None) != (self.tool_call_id is None):
            raise ValueError(
                "request_id and tool_call_id must either both be present or both be None"
            )


@dataclass(frozen=True)
class ToolResultReceived(AgentEvent):
    request_id: str


@dataclass(frozen=True)
class Failed(AgentEvent):
    reason: str
    recoverable: bool

@dataclass(frozen=True)
class Recover(AgentEvent):
    pass #empty event, event is atomic itself.


class Error(AgentEvent):
    recoverable: bool