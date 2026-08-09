import asyncio
import uuid
from dataclasses import dataclass, field


# primitive ops: legal moves on the carrier, still just data — no event type appears here
@dataclass
class CommandQueueState:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    queue: asyncio.Queue = field(default_factory=asyncio.Queue)
