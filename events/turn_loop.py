from dataclasses import dataclass

from events.base import Event


# Internal to Turn loop events.
@dataclass(frozen=True)
class TurnLoopEvent(Event):
    """E_cmd — abstract base; never constructed directly, only its variants below."""


@dataclass(frozen=True)
class Start(TurnLoopEvent):
    request_id: str


@dataclass(frozen=True)
class CompletionReceived(TurnLoopEvent):
    request_id: str | None
    tool_call_id: str | None

    def __post_init__(self) -> None:
        if (self.request_id is None) != (self.tool_call_id is None):
            raise ValueError(
                "request_id and tool_call_id must either both be present or both be None"
            )


@dataclass(frozen=True)
class ToolResultReceived(TurnLoopEvent):
    request_id: str


@dataclass(frozen=True)
class Failed(TurnLoopEvent):
    reason: str
    recoverable: bool


@dataclass(frozen=True)
class Recover(TurnLoopEvent):
    pass  # empty event, event is atomic itself.


class Error(TurnLoopEvent):
    recoverable: bool
