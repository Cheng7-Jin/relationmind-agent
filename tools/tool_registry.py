from tools.emotion_tools import AnalyzeEmotionTool
from tools.memory_tools import SaveMemoryTool
from tools.knowledge_tool import KnowledgeRetrieveTool
from utils.logger import get_logger

logger = get_logger("ToolRegistry")

class ToolRegistry:
    tools = {
        "analyze_emotion": AnalyzeEmotionTool(),
        "save_memory": SaveMemoryTool(),
        "knowledge_retrieve": KnowledgeRetrieveTool(),
    }

    @staticmethod
    def get_tool(name):
        tool = ToolRegistry.tools.get(name)
        if not tool:
            logger.warning(f"未找到工具: {name}")
        return tool

    @staticmethod
    def get_tool_names():
        return list(ToolRegistry.tools.keys())

    @staticmethod
    def get_tool_definitions():
        return [
            {
                "type": "function",
                "function": {
                    "name": "analyze_emotion",
                    "description": "分析用户当前情绪状态（开心、难过、焦虑、愤怒、孤独、中性）",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "user_input": {"type": "string", "description": "用户输入的对话内容"}
                        },
                        "required": ["user_input"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "save_memory",
                    "description": "保存用户对话、情绪、依恋风格到长期情感记忆库",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "user_input": {"type": "string", "description": "用户输入内容"},
                            "emotion": {"type": "string", "description": "识别出的用户情绪"},
                            "attachment_style": {"type": "string", "description": "用户依恋风格"}
                        },
                        "required": ["user_input", "emotion", "attachment_style"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "knowledge_retrieve",
                    "description": "从心理学、情感疏导、依恋理论、陪伴沟通技巧知识库检索专业知识，用于科学、温暖、有依据地回复用户",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "检索关键词，如：焦虑疏导、孤独缓解、依恋沟通、非暴力沟通等"}
                        },
                        "required": ["query"]
                    }
                }
            }
        ]