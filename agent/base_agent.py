from abc import ABC, abstractmethod
from schema.message import AgentMessage
from utils.logger import get_logger
from utils.middleware import log_message
import time

logger = get_logger("BaseAgent")

class BaseAgent(ABC):
    def __init__(self, llm, memory=None):
        self.llm = llm
        self.memory = memory
        self.name = self.__class__.__name__

    @abstractmethod
    def execute(self, message: AgentMessage):
        pass

    @log_message
    def run(self, message: AgentMessage):
        start = time.time()
        
        # 记录进入步骤
        message.workflow_trace.append(f"enter:{self.name}")
        
        # 执行
        result = self.execute(message)
        
        # 记录耗时
        duration = time.time() - start
        message.workflow_duration += duration
        message.step_results[self.name] = "success"
        
        logger.info(f"{self.name} 执行完成，耗时：{duration:.2f}s")
        return result