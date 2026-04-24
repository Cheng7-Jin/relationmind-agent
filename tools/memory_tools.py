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