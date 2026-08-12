from dataclasses import dataclass

from type_states.agent import AwaitingTool, Idle, Running, TurnLoopState

from event_bus import EventBusManager
from events.event_bus import Publish
from events.Session import TurnStateChanged
from events.turn_loop import (
    CompletionReceived,
    Error,
    Failed,
    Recover,
    Start,
    ToolResultReceived,
    TurnLoopEvent,
)
from monads import Err, Ok, Result
from states.event_bus import EventBusState


@dataclass(frozen=True)
class IllegalTransition:
    message: str


# TODO resolve splitting TurnLoopState within TurnLoopState by subset inclusion some where
class TurnManager:
    @staticmethod
    def apply(
        state: TurnLoopState, event_bus_state: EventBusState, event: TurnLoopEvent
    ) -> Result[TurnLoopState, IllegalTransition]:
        match event, state:
            case Start(request_id=rid), Idle():
                # Eventbus, Current turnloop state -> Next turnloop state.
                return TurnManager._transition(
                    event_bus_state, state, Running(request_id=rid)
                )
            case CompletionReceived(request_id=rid, tool_call_id=tc), Running() if (
                tc is not None
            ):
                return TurnManager._transition(
                    event_bus_state,
                    state,
                    AwaitingTool(request_id=rid, pending_tool_call=tc),
                )
            case CompletionReceived(), Running():
                return TurnManager._transition(event_bus_state, state, Idle())
            case ToolResultReceived(request_id=rid), AwaitingTool():
                return TurnManager._transition(
                    event_bus_state, state, Running(request_id=rid)
                )
            case Failed(reason=r, recoverable=rec), _:
                return TurnManager._transition(
                    event_bus_state, state, Error(reason=r, recoverable=rec)
                )
            # Domain Event not a transition induced event.
            case Recover(), Error(recoverable=True):
                return TurnManager._transition(event_bus_state, state, Idle())
            case _:
                return Err(
                    IllegalTransition(
                        f"{type(event).__name__} illegal from {type(state).__name__}"
                    )
                )

    @staticmethod
    def _transition(
        event_bus_state: EventBusState, previous: TurnLoopState, current: TurnLoopState
    ) -> Result[TurnLoopState, IllegalTransition]:
        # emit event
        EventBusManager.apply(
            event_bus_state,
            Publish(
                payload=TurnStateChanged(
                    previous=type(previous).__name__, current=type(current).__name__
                )
            ),
        )
        return Ok(current)
