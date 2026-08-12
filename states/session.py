from dataclasses import dataclass

from states.worker_runtime import WorkerRuntimeState

from states.command_queue import CommandQueueState
from states.event_bus import EventBusState
from type_states.turn_loop import TurnLoopState


@dataclass
class SessionState:
    turn_loop_state: TurnLoopState
    workers_state: WorkerRuntimeState
    command_queue_state: CommandQueueState
    event_bus_state: EventBusState
