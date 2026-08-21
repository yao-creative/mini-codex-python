from abc import ABC, abstractmethod
from typing import Any
from monads import Err
import session
import persistence
from runtime import Runtime
from events.base import Event, ExternalEvent
from commands.command import Command
from monads import Result, Ok, Err
from command_queue import CommandQueueManager
from states.app import AppState

from dataclasses import dataclass

@dataclass(frozen=True)
class CoreEngineError:
    message: str

class CoreEngineInterface(ABC):
    @staticmethod
    @abstractmethod
    def run(app_state):
        """
        Run the core engine with the given AppState.
        This method should be overridden by implementations
        to provide the main execution logic.
        """
        pass

    @staticmethod
    @abstractmethod
    def apply(command: Command, app_state: AppState):
        """
        Run the core engine with the given AppState.
        This method should be overridden by implementations
        to provide the main execution logic.
        """
        pass


class CoreEngine(CoreEngineInterface):
    @staticmethod
    def run(app_state: AppState)-> Result[None, CoreEngineError]:
        while True:
            command_queue_state = app_state.command_queue_state
            cmd: Command = CommandQueueManager.dequeue(command_queue_state)
            event = await CoreEngine.apply(cmd, app_state)
            await EventBusManager.enqueue(command_queue_state, )



        
            