from commands.command import Command
from dataclasses import dataclass
from events.command_queue import (
    Cancel,
    Clear,
    CommandQueueEvent,
    Dequeue,
    Enqueue,
    Requeue,
)
from monads import Err, Ok, Result
from states.command_queue import CommandQueueState


@dataclass(frozen=True)
class QueueEmpty:
    pass


@dataclass(frozen=True)
class CommandNotFound:
    command_id: str


class CommandQueueManager:
    # mutation on CommandQueueState
    # mutation/ evaluator state x event -> state mutated OR (state AND Command) OR (State AND None) OR (State AND Error). an event is a function on state.
    @staticmethod
    def apply(
        state: CommandQueueState, event: CommandQueueEvent
    ) -> Result[Command | None, QueueEmpty | CommandNotFound]:
        match event:
            case Enqueue(command=cmd):
                return CommandQueueManager.enqueue(state, cmd)
            case Dequeue():
                return CommandQueueManager.dequeue(state)
            case Cancel(command_id=command_id):
                return CommandQueueManager.cancel(state, command_id)
            case Clear():
                return CommandQueueManager.clear(state)
            case Requeue(command=cmd, to_front=to_front):
                if to_front:
                    return CommandQueueManager.enqueue_front(state, cmd)
                else:
                    return CommandQueueManager.enqueue(state, cmd)

    # mutations
    @staticmethod
    def enqueue(state: CommandQueueState, cmd: Command) -> None:
        state.queue.append(cmd)

    @staticmethod
    def dequeue(state: CommandQueueState) -> Result[Command, QueueEmpty]:
        if not state.queue:
            # queue is empty
            return Err(QueueEmpty())
        return Ok(state.queue.popleft())

    @staticmethod
    def cancel(
        state: CommandQueueState, command_id: str
    ) -> Result[None, CommandNotFound]:
        """
        Remove a specific command from the queue by its id.
        Returns True if a command was removed, False otherwise.
        """
        for idx, cmd in enumerate(state.queue):
            if getattr(cmd, "id", None) == command_id:
                del state.queue[idx]
                return Ok(None)
        return Err(CommandNotFound())

    # Guaranteed state of None if cleared
    @staticmethod
    def clear(state: CommandQueueState) -> Result(None):
        """Removes all commands from the queue."""
        state.queue.clear()
        return Ok(None)

    @staticmethod
    def enqueue_front(state: CommandQueueState, cmd: Command) -> None:
        """Adds a command to the front of the queue."""
        state.queue.appendleft(cmd)
        return Ok(None)
