
from dataclasses import dataclass
from type_states.base import TypeState


# Type states: small category where states are objects themselves and not mutable states
@dataclass(frozen=True)
class AgentTypeState(TypeState):
    pass

@dataclass(frozen=True)
class Idle(AgentTypeState):
    pass

@dataclass(frozen=True)
class Running(AgentTypeState):
    request_id: str          # handle to the in-flight LLM call — prevents double-dispatch (typestate point)

@dataclass(frozen=True)
class AwaitingTool(AgentTypeState):
    request_id: str          # the LLM turn this tool call belongs to
    pending_tool_call: str   # id of the ToolCall dispatched to WorkerManager

@dataclass(frozen=True)
class Error(AgentTypeState):
    reason: str
    recoverable: bool

AgentState = Idle | Running | AwaitingTool | Error