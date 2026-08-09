from abc import ABC, abstractmethod
from collections.abc import Iterable

from states.agent_manager import AgentManager
from states.core_state import CoreState
from states.worker_manager import WorkerManager

from events.base import Event
from events.command_queue import CommandQueueEvent
from states.app import AppState
from states.command_queue import CommandQueueManager
from states.event_bus import EventBusManager


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

    # constructor case for Even driven core.
    @staticmethod
    def apply(state: CoreState, event: Event):
        # OR disjunction of matching managers to events
        manager = Core._MANAGERS[type(event)]
        factor = getattr(state, manager.FIELD)
        manager.transition(factor, event)

    @staticmethod
    def run(state: CoreState, events: Iterable[Event]) -> AppState:
        for e in events:
            state = Core.apply(state, e)
        return state
