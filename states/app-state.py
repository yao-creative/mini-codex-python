from dataclasses import dataclass, field
from datetime import datetime
import uuid

from states.config import Config  

@dataclass
class AppState:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.utcnow)
    config: Config = field(default=None)