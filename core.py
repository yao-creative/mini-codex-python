

from abc import ABC, abstractmethod
import asyncio
from states.app import AppState
from states.core_state import CoreState
from collections.abc import Iterable
from events.event import Event
from states.command_queue import CommandQueueManager
from states.event_bus import EventBusManager
from states.agent_manager import AgentManager
from states.worker_manager import WorkerManager


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
    _MANAGERS = {
        CommandQueueEvent: CommandQueueManager,
        EventBusEvent: EventBusManager,
        AgentEvent: AgentManager,
        WorkerEvent: WorkerManager,
    }

    def __init__(self):
        pass 

    # constructor case for Even driven core.
    @abstractmethod
    def step(self, state: CoreState, event: Event):
        # OR disjunction of matching managers to events
        manager = Core._MANAGERS[type(event)]
        factor = getattr(state, manager.FIELD)
        manager.transition(factor, event) 


    @staticmethod
    def run(state: CoreState, events: Iterable[Event]) -> AppState:
        for e in events:
            state = Core.step(state, e)
        return state
