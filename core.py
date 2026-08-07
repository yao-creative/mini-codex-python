

from abc import ABC, abstractmethod
import asyncio
from states.app_state import AppState


class CoreInterface(ABC):
    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def run(self):
        pass

class Core(CoreInterface):
    def __init__(self):
        self.command_queue = asyncio.Queue()
        self.event_bus = EventBus()
        self.agent = AgentRuntime()
        self.workers = WorkerRuntime()
        
    def run(self, AppState):
        # Main logic to run the core functionality
        pass