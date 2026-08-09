from abc import ABC, abstractmethod

from states.event_bus import EventBusState
from events.event_bus import EventBusEvent, Publish, Unsubscribe
from monads import Result, Ok



from dataclasses import dataclass

@dataclass(frozen=True)
class DuplicateSubscriber:
    reader_id: str

@dataclass(frozen=True)
class UnknownSubscriber:
    reader_id: str



class EventBusManagerInterface(ABC):
    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    async def apply(self, event):
        pass

class EventBusManager(EventBusManagerInterface):
    @staticmethod
    def apply(state: EventBusState, event: EventBusEvent)-> Result[None, DuplicateSubscriber | UnknownSubscriber]:
        
        match event:
            case Publish(payload= p):
                return EventBusManager.publish(state= state)
            case Subscribe(reader_id=rid, start_from=start)

    @staticmethod
    def publish(state: EventBusState, payload: EventPayload) -> Result(None):
        state.log.append()
        return Ok(None)

    @staticmethod
    def subscribe(state: EventBusState, reader_id: str, start_from: int) -> Result[None, DuplicateSubscriber| UnknownSubscriber]:
        state.





