from tools.base_tool import BaseTool
from schema.message import AgentMessage
from utils.logger import get_logger

logger = get_logger("MemoryTools")

class SaveMemoryTool(BaseTool):
    name = "save_memory"
    description = "保存用户对话记忆"

    def run(self, message: AgentMessage):
        try:
            message.memory.save_memory(
                message.user_input,
                message.emotion,
                message.attachment_style
            )
            logger.info("记忆保存成功")
        except Exception as e:
            logger.error(f"保存记忆失败: {e}", exc_info=True)

class RetrieveMemoryTool(BaseTool):
    name = "retrieve_memory"
    description = "检索用户历史记忆"

    def run(self, message: AgentMessage):
        try:
            memories = message.memory.retrieve_memory(message.user_input)
            logger.info(f"检索到记忆: {len(memories)}条")
            return memories
        except Exception as e:
            logger.error(f"检索记忆失败: {e}", exc_info=True)
            return []