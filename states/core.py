from dataclasses import dataclass

from type_states.agent import AgentState

from states.command_queue import CommandQueueState
from states.conversation_runtime import ConversationRuntimeState
from states.event_bus import EventBusState
from states.worker_runtime import WorkerRuntimeState


@dataclass
class CoreState:
    agent_state: AgentState
    conversation_state: ConversationRuntimeState
    workers_state: WorkerRuntimeState
    command_queue_state: CommandQueueState
    event_bus_state: EventBusState
