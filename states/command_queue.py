from dataclasses import dataclass, field
import uuid
import asyncio


# primitive ops: legal moves on the carrier, still just data — no event type appears here
@dataclass
class CommandQueueState:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    queue: asyncio.Queue = field(default_factory=asyncio.Queue)

    def enqueue(self, cmd: Command) -> None:
        self.queue.append(cmd)

    def dequeue(self) -> Command | None:
        return self.queue.pop(0) if self.queue else None

    def cancel(self, command_id: str) -> bool:
        """
        Remove a specific command from the queue by its id.
        Returns True if a command was removed, False otherwise.
        """
        for idx, cmd in enumerate(self.queue):
            if getattr(cmd, 'id', None) == command_id:
                del self.queue[idx]
                return True
        return False

    def clear(self) -> None:
        """Removes all commands from the queue."""
        self.queue.clear()

    def enqueue_front(self, cmd: 'Command') -> None:
        """Adds a command to the front of the queue."""
        self.queue.insert(0, cmd)
   