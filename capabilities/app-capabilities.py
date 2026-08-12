from dataclasses import dataclass
from typing import TypeVar

from adapters.llm import LLMAadapter
from adapters.storage import Storage
from states.event_bus import EventBusState
from monads import Reader

T = TypeVar("T")

# EventSink type — for now, this is hereby defined as EventBusState
EventSink = EventBusState


@dataclass(frozen=True)
class AppCapabilities:
    storage: Storage
    model: LLMAadapter
    events: EventSink

AppReader = Reader[AppCapabilities, T]