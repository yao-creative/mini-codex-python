from abc import ABC, abstractmethod

class EventBusManagerInterface(ABC):
    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    async def publish(self, event):
        pass

class EventBusManager(EventBusManagerInterface):
    def __init__(self):
        pass

    @staticmethod
    async def publish(self, event_bus_state: EventBusState, event: Event):
        for subscriber in self.subscribers:
            await subscriber(event)