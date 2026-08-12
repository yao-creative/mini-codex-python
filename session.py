from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import assert_never

from command_queue import CommandQueueManager
from event_bus import EventBusManager
from events.base import Event
from events.command_queue import CommandQueueEvent
from events.event_bus import EventBusEvent
from events.turn_loop import TurnLoopEvent
from states.app import AppState
from states.session import SessionState
from turn import TurnManager


class SessionInterface(ABC):
    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def run(self, state: SessionState):
        pass

    @abstractmethod
    def step(self, state: SessionState, event: Event):
        pass


class Session(SessionInterface):
    # constructor case for Even driven Session.
    @staticmethod
    def apply(state: SessionState, event: Event):
        # OR disjunction of matching managers to events\
        match event:
            case CommandQueueEvent():
                # domain: S_cmd × S_bus — matches CommandQueueManager's actual signature
                # TODO figure out if need to add event bus emission
                return CommandQueueManager.apply(
                    state.command_queue_state, state.event_bus_state, event
                )
                # domain: S_bus only — EventBusManager never needed to widen
            case EventBusEvent():
                # domain: S_agent × S_bus, by the same publish-on-transition logic as CommandQueue
                return EventBusManager.apply(state.event_bus_state, event)
            case TurnLoopEvent():  # define this or
                # TODO figure out if need to add event bus emission
                return TurnManager.apply(
                    state.turn_loop_state, state.event_bus_state, event
                )
            case _:  # only 3 disjunct case.
                assert_never(event)

    @staticmethod
    def run(state: SessionState, events: Iterable[Event]) -> AppState:
        for e in events:
            state = Session.apply(state, e)
        return state
