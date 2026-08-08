from dataclasses import dataclass, field
from uuid import uuid4
from datetime import datetime

@dataclass(frozen=True)
class Event:
    id: str = field(default_factory=lambda: str(uuid4()))
    created_at: datetime = field(default_factory=datetime.utcnow)