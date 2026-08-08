from dataclasses import dataclass
from events.base import Event
from states.command_queue import Command

@dataclass(frozen=True)
class CommandQueueEvent(Event):
    """E_cmd — abstract base; never constructed directly, only its variants below."""


@dataclass(frozen=True)
class Enqueue(CommandQueueEvent):
    command: Command

@dataclass(frozen=True)
class Dequeue(CommandQueueEvent):
    """No payload — the queue's own FIFO order determines what's removed."""
    pass


@dataclass(frozen=True)
class Cancel(CommandQueueEvent):
    """Remove a specific in-flight command by id, out of FIFO order."""
    command_id: str



@dataclass(frozen=True)
class Clear(CommandQueueEvent):
    """Drop everything currently queued."""
    pass


@dataclass(frozen=True)
class Requeue(CommandQueueEvent):
    """Move a command back onto the queue — e.g. after a failed dequeue/dispatch."""
    command: Command
    to_front: bool = False