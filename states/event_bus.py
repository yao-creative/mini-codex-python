from dataclasses import dataclass, field
from typing import Callable, TypeVar, Generic

from events.event import Event

T = TypeVar('T', bound=Event)
Handler = Callable[[T], None]


@dataclass
class EventBusState:
    subscribers: dict[type[Event], list[Handler]] 