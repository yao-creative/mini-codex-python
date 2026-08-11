from abc import ABC, abstractmethod

class Adapter(ABC):
    @abstractmethod
    def request(endpoint: str, payload: str):
        pass 