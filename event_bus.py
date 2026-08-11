from abc import ABC, abstractmethod
from dataclasses import dataclass

from events.event_bus import (
    EventBusEvent,
    EventPayload,
    Publish,
    Subscribe,
    Unsubscribe,
)
from monads import Err, Ok, Result
from states.event_bus import EventBusState


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


# Intentionally atomic methods. But have to watch out for mid flight: subscribe - poll - unsubcribe vs subscribe - unsubscribe - poll when we want to change the user cursor
class EventBusManager(EventBusManagerInterface):
    @staticmethod
    def apply(
        state: EventBusState, event: EventBusEvent
    ) -> Result[None, DuplicateSubscriber | UnknownSubscriber]:

        match event:
            case Publish(payload=payload):
                return EventBusManager.publish(state=state, payload=payload)
            case Subscribe(reader_id=reader_id, start_from=start_from):
                return EventBusManager.subscribe(
                    state=state, reader_id=reader_id, start_from=start_from
                )

            case Unsubscribe(reader_id=reader_id):
                return EventBusManager.unsubscribe(state=state, reader_id=reader_id)

    @staticmethod
    def publish(state: EventBusState, payload: EventPayload) -> Result(None):
        state.log.append()
        return Ok(None)

    @staticmethod
    def subscribe(
        state: EventBusState, reader_id: str, start_from: int
    ) -> Result[None, DuplicateSubscriber]:
        if reader_id in state.cursors:
            return Err(DuplicateSubscriber())

        state.cursors[reader_id] = start_from
        return Ok(None)

    @staticmethod
    def unsubscribe(
        state: EventBusState, reader_id: str
    ) -> Result[None, UnknownSubscriber]:
        if reader_id in state.cursors:
            del state.cursors[reader_id]
            return Ok(None)
        return Err(UnknownSubscriber())
