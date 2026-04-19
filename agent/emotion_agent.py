from agent.base_agent import BaseAgent
from schema.message import AgentMessage
from tools.tool_registry import ToolRegistry
from utils.retry import retry

class EmotionAgent(BaseAgent):
    @retry(max_retries=2)
    def execute(self, message: AgentMessage):
        tool = ToolRegistry.get_tool("analyze_emotion")
        # ========================
        # 修复：只传 message
        # ========================
        emotion = tool.run(message)
        message.emotion = emotion
        message.tools_used.append(tool.name)
        return message