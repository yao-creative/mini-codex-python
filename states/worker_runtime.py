import uuid
from dataclasses import dataclass, field
from datetime import datetime
from states.base import BaseState



@dataclass
class WorkerRuntimeState(BaseState):
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.utcnow)
