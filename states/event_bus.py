from collections import deque
from collections.abc import Callable
from dataclasses import dataclass
from typing import TypeVar

from events.base import Event

T = TypeVar("T", bound=Event)
Handler = Callable[[T], None]


@dataclass
class EventBusState:
    log: deque[Event]
    cursors: dict[str, int]
