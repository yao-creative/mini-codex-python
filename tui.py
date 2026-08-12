from abc import ABC, abstractmethod
from states.event_bus import EventBusState
from events.event_bus import Subscribe
from event_bus import EventBusManager
from monads import Result

class TuiInterface(ABC):
    @abstractmethod
    @staticmethod
    async def run_loop():
        pass


class Tui(TuiInterface):
    @staticmethod
    async def run_loop(event_bus_state: EventbusState): -> Result[None]
        EventBusManager.apply(event_bus_state, Subscribe(reader_id="tui-render", start_from=None)) 
        async for keypress in read_keys():                       # impure source
            sink(keypress_to_event(keypress))                     # -> CommandQueueEvent, e.g. Enqueue(user_prompt)
            await drain_and_render(bus)   
                                     # poll -> render, impure sink
    async def drain_and_render(bus: EventBusState) -> None:
        while True:
            result = EventBusManager.poll(bus, "tui-render")
            match result:
                case Ok(value=fact): render(fact)                  # dumb — no domain logic, just display
                case Err(error=NoNew()): return
