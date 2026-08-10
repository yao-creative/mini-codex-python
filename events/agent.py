from dataclasses import dataclass

from type_states.turn_loop import TurnLoopState


@dataclass(frozen=True)
class AgentEvent:
    pass 


@dataclass(frozen=True)
class AgentStateChanged(AgentEvent):
    previous: TurnLoopState
    current: TurnLoopState
