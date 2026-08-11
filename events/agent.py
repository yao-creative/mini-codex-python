from dataclasses import dataclass

from type_states.turn_loop import TurnLoopState


@dataclass(frozen=True)
class AgentEvent:
    pass 


@dataclass(frozen=True)
class AgentStateChanged(AgentEvent):
    request_id: str
    previous: str            # tag name of the prior TurnLoopState variant
    current: TurnLoopState   # the full value — Running(request_id=...) or AwaitingTool(...) etc.
    caused_by: str | None = None