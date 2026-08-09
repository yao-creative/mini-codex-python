from dataclasses import dataclass

from events.base import Event



@dataclass(frozen=True)
class EventBusEvent(Event):
    pass



# TODO: Define EventPayload type or class according to the requirements of EventBus events.
# For now, this is a placeholder and must be replaced/implemented.
EventPayload = object

@dataclass(frozen=True)
# the fact being broadcast — this IS the thing every subscriber will eventually poll
@dataclass(frozen=True)
class Publish(EventBusEvent):
    payload: EventPayload  # the fact being broadcast — this IS the thing every subscriber will eventually poll


@dataclass(frozen=True)
class Subscribe(EventBusEvent):
    reader_id: str  # who's registering
    start_from: int | None = (
        None  # None = start at current log length (only future events);
    )
    # 0 = replay full history; explicit N = resume from a known offset


@dataclass(frozen=True)
class Unsubscribe(Event):
    reader_id: str
    # who's leaving — enough to drop the cursor entry
