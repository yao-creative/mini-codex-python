from dataclasses import dataclass, field

from states.agent_runtime import AgentRuntimeState
from states.conversation_runtime import ConversationRuntimeState
from states.worker_runtime import WorkerRuntimeState
from states.command_queue import CommandQueueState
from states.event_bus import EventBusState

@dataclass
class Core:
    agent_state: AgentRuntimeState
    conversation_state: ConversationRuntimeState
    workers_state: WorkerRuntimeState
    command_queue_state: CommandQueueState
    event_bus_state: EventBusState