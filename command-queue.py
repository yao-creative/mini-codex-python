
from states.command_queue import CommandQueueState
from events.command_queue import CommandQueueEvent

class CommandQueueManager:
    #mutation on CommandQueueState
    @staticmethod
    def transition(state: CommandQueueState, event: CommandQueueEvent) -> None:
        match event:
            case CommandQueueEvent.Enqueue(cmd):
                state.queue.append(cmd)
            case CommandQueueEvent.Dequeue():
                state.dequeue()
            case 