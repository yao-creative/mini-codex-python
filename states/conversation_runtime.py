from dataclasses import dataclass, field

from states.agent_runtime import AgentRuntime
from states.conversation_runtime import ConversationRuntime
from states.worker_runtime import WorkerRuntime
from states.command_queue import CommandQueue
from states.event_bus import EventBus

@dataclass
class Core:
    agent: AgentRuntime
    conversation: ConversationRuntime
    workers: WorkerRuntime
    command_queue: CommandQueue
    event_bus: EventBus