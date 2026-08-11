from abc import ABC, abstractmethod
from events.base import Event
from events.agent import AgentStateChanged
from monads import Result, Ok, Err
from event_bus import EventBusManager 
from states.event_bus import EventBusState
import asyncio




class TurnLoopRunnerInterface(ABC):
    @abstractmethod
    def run()  -> Result[None]:
        pass

    @abstractmethod
    def _invoke_llm(event: AgentStateChanged):
        pass

class TurnLoopRunner(TurnLoopRunnerInterface):

    #start infinite loop:
    # no imports no default values, all values come from config.
    @staticmethod
    async def run_forever(event_bus_state: EventBusState, polling_interval = int) -> Result[None]:
        while True:
            result = EventBusManager.poll(event_bus_state, "turnloop-runner")
            match result:
                case Ok(value= AgentStateChanged(current = "Running") as fact):
                    return await TurnLoopRunner._invoke_llm(fact)
                case Ok(value=_):
                    pass
                case Err(error=NoNew()):
                    return await asyncio.sleep() #polling interval

    @staticmethod
    async def _invoke_llm(fact: AgentStateChanged) -> None:
        #TODO figure out llm completion
        completion = "ok" #stubbed



