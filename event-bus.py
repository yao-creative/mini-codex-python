from abc import ABC, abstractmethod

class EventBusInterface(ABC):
    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    async def publish(self, event):
        pass

class EventBus(EventBusInterface):
    def __init__(self, subscribers):
        self.subscribers = []

    async def publish(self, event):
        for subscriber in self.subscribers:
            await subscriber(event)