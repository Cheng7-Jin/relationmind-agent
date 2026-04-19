from schema.message import AgentMessage
from utils.logger import get_logger

logger = get_logger("middleware")

def log_message(func):
    def wrapper(instance, message: AgentMessage):
        logger.info(f"[{message.sender} → {message.receiver}] {message.user_input}")
        return func(instance, message)
    return wrapper