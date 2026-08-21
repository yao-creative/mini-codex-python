import uuid
from dataclasses import dataclass, field
from datetime import datetime

from states.config import Config
from states.session import SessionState
from states.command_queue import CommandQueueState

@dataclass
class AppState:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.utcnow)
    config: Config = field(default=None)
    command_queue_state: CommandQueueState = field(default=None)
    session_state: SessionState = field(default=None)
