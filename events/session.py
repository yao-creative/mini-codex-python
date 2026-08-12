from dataclasses import dataclass

from events.base import Event


@dataclass(frozen=True)
class SessionEvent(Event):
    pass


@dataclass(frozen=True)
class TurnStateChanged(SessionEvent):
    previous: str
    current: str
