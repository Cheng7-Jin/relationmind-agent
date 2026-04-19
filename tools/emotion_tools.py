from tools.base_tool import BaseTool
from schema.message import AgentMessage
from prompt.emotion_prompt import EMOTION_PROMPT
from utils.logger import get_logger

logger = get_logger("EmotionTools")

class AnalyzeEmotionTool(BaseTool):
    name = "analyze_emotion"
    description = "分析用户情绪"

    def run(self, message: AgentMessage):
        try:
            prompt = EMOTION_PROMPT.format(text=message.user_input)
            res = message.llm.invoke(prompt).content.strip()
            logger.info(f"情绪分析结果: {res}")
            return res
        except Exception as e:
            logger.error(f"情绪分析失败: {e}", exc_info=True)
            return "中性"