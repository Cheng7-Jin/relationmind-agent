from abc import ABC, abstractmethod
from schema.message import AgentMessage

class BaseTool(ABC):
    name: str
    description: str

    @abstractmethod
    def run(self, message: AgentMessage):
        pass