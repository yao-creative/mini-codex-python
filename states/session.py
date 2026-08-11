from dataclasses import dataclass

from states.conversation_runtime import ConversationRuntimeState
from states.worker_runtime import WorkerRuntimeState
from type_states.turn_loop import TurnLoopState

from states.command_queue import CommandQueueState
from states.event_bus import EventBusState


@dataclass
class SessionState:
    turn_loop_state: TurnLoopState
    workers_state: WorkerRuntimeState
    command_queue_state: CommandQueueState
    event_bus_state: EventBusState
