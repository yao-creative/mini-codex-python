from dataclasses import dataclass, field
from datetime import datetime
import uuid

@dataclass
class AgentRuntimeState:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.utcnow)