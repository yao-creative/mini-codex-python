from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import assert_never

from agent import AgentManager

from command_queue import CommandQueueManager
from event_bus import EventBusManager
from events.agent import AgentEvent
from events.base import Event
from events.command_queue import CommandQueueEvent
from events.event_bus import EventBusEvent
from states.app import AppState
from states.core import CoreState


class CoreInterface(ABC):
    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def run(self, state: CoreState):
        pass

    @abstractmethod
    def step(self, state: CoreState, event: Event):
        pass


class Core(CoreInterface):
    # constructor case for Even driven core.
    @staticmethod
    def apply(state: CoreState, event: Event):
        # OR disjunction of matching managers to events\
        match event:
            case CommandQueueEvent():
                # domain: S_cmd × S_bus — matches CommandQueueManager's actual signature
                # TODO figure out if need to add event bus emission
                return CommandQueueManager.apply(state.command_queue_state, state.event_bus_state, event)
                # domain: S_bus only — EventBusManager never needed to widen
            case EventBusEvent():
                # domain: S_agent × S_bus, by the same publish-on-transition logic as CommandQueue
                return EventBusManager.apply(state.event_bus_state, event)
            case AgentEvent(): # define this or 
                # TODO figure out if need to add event bus emission
                return AgentManager.apply(state.agent_state, state.event_bus_state, event)
            case _:  # only 3 disjunct case.
                assert_never(event)

    @staticmethod
    def run(state: CoreState, events: Iterable[Event]) -> AppState:
        for e in events:
            state = Core.apply(state, e)
        return state
