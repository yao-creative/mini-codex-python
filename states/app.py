import uuid
from dataclasses import dataclass, field
from datetime import datetime

from states.config import Config
from states.core import CoreState


@dataclass
class AppState:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.utcnow)
    config: Config = field(default=None)
    core_state: CoreState = field(default=None)
