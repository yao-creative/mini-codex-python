from dataclasses import dataclass

from type_states.agent import AgentState, AwaitingTool, Idle, Running

from event_bus import EventBusManager
from events.agent import AgentStateChanged
from events.event_bus import Publish
from events.turn_loop import (
    TurnLoopEvent,
    CompletionReceived,
    Error,
    Failed,
    Recover,
    Start,
    ToolResultReceived,
)
from monads import Err, Ok, Result
from states.event_bus import EventBusState


@dataclass(frozen=True)
class IllegalTransition:
    message: str



# TODO resolve splitting TurnLoopState within AgentState by subset inclusion some where
class AgentManager:
    @staticmethod
    def apply(
        state: AgentState, event_bus_state: EventBusState, event: TurnLoopEvent
    ) -> Result[AgentState, IllegalTransition]:
        match event, state:
            case Start(request_id=rid), Idle():
                # Eventbus, Current turnloop state -> Next turnloop state.
                return AgentManager._transition(
                    event_bus_state, state, Running(request_id=rid)
                )
            case CompletionReceived(request_id=rid, tool_call_id=tc), Running() if (
                tc is not None
            ):
                return AgentManager._transition(
                    event_bus_state,
                    state,
                    AwaitingTool(request_id=rid, pending_tool_call=tc),
                )
            case CompletionReceived(), Running():
                return AgentManager._transition(event_bus_state, state, Idle())
            case ToolResultReceived(request_id=rid), AwaitingTool():
                return AgentManager._transition(
                    event_bus_state, state, Running(request_id=rid)
                )
            case Failed(reason=r, recoverable=rec), _:
                return AgentManager._transition(
                    event_bus_state, state, Error(reason=r, recoverable=rec)
                )
            # Domain Event not a transition induced event.
            case Recover(), Error(recoverable=True):
                return AgentManager._transition(event_bus_state, state, Idle())
            case _:
                return Err(
                    IllegalTransition(
                        f"{type(event).__name__} illegal from {type(state).__name__}"
                    )
                )

    @staticmethod
    def _transition(
        event_bus_state: EventBusState, previous: AgentState, current: AgentState
    ) -> Result[AgentState, IllegalTransition]:
        # emit event
        EventBusManager.apply(
            event_bus_state,
            Publish(
                payload=AgentStateChanged(
                    previous=type(previous).__name__, current=type(current).__name__
                )
            ),
        )
        return Ok(current)
