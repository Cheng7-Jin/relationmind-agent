from agent.base_agent import BaseAgent
from schema.message import AgentMessage
from tools.tool_registry import ToolRegistry
from ego_mcp import EgoMCP
import json
from utils.logger import get_logger
from config.langsmith import trace_agent

# ✅ 关系成长系统（记忆检索、权重、自动清理）
from memory_system import (
    retrieve_with_relation,
    update_memory_weight,
    auto_clean_low_weight_memory,
    get_tone_by_user
)

logger = get_logger("MainAgent")

class MainAgent(BaseAgent):
    def __init__(self, llm, memory, emotion_agent, attach_agent, response_agent):
        super().__init__(llm, memory)
        self.emotion_agent = emotion_agent
        self.attach_agent = attach_agent
        self.response_agent = response_agent
        self.tools = ToolRegistry()

        # ============================
        # ✅ 强化版 EGO-MCP 心智大脑
        # ============================
        self.ego = EgoMCP()

    # ============================
    # ✅ LLM 自主决策工具调用（升级：支持知识检索）
    # ============================
    def tool_calling(self, message: AgentMessage):
        tools_def = self.tools.get_tool_definitions()

        prompt = f"""
用户输入：{message.user_input}
可使用工具：{json.dumps(tools_def, ensure_ascii=False)}

判断规则：
1. 任何情况 → 必须调用 analyze_emotion（分析情绪）
2. 有历史 → 必须调用 retrieve_memory（读取记忆）
3. 负面情绪（难过/焦虑/愤怒/孤独）→ 必须调用 knowledge_retrieve（查专业疏导知识）
4. 中性情绪 → 可不调用知识检索
只返回 JSON 数组，例如：["analyze_emotion","retrieve_memory","knowledge_retrieve"]
不要任何多余文字。
"""

        try:
            res = self.llm.invoke(prompt).content.strip()
            return json.loads(res)
        except Exception as e:
            logger.warning(f"工具调用解析失败：{e}")
            return ["analyze_emotion", "retrieve_memory"]

    # ======================
    # ✅ 关键：给核心执行函数加追踪装饰器
    # ======================
    @trace_agent
    def execute(self, message: AgentMessage):
        try:
            message.llm = self.llm
            message.memory = self.memory

            user_input = message.user_input
            logger.info(f"用户输入：{user_input}")

            # ============================
            # ✅ MCP 心智：情绪 & 安全检测
            # ============================
            self.ego.update_emotion(user_input)
            safety_risk = self.ego.check_safety(user_input)  # 风险检测
            if safety_risk:
                message.response = "我很担心你，请一定寻求身边的人或专业心理咨询师帮助，你值得被好好照顾。"
                message.status = "completed"
                return message

            # ============================
            # ✅ 工具决策 & 执行
            # ============================
            selected_tools = self.tool_calling(message)
            message.tools_used = selected_tools
            logger.info(f"LLM 选择工具：{selected_tools}")

            # 1. 情绪分析
            if "analyze_emotion" in selected_tools:
                message = self.emotion_agent.run(message)
                logger.info(f"情绪结果：{message.emotion}")

            # 2. 记忆检索（带关系等级 + 遗忘机制 + 权重强化）
            if "retrieve_memory" in selected_tools:
                # 🔥 增强版记忆检索（支持权重、遗忘、等级）
                memories = retrieve_with_relation(message.user_id, message.user_input)
                message.retrieved_memories = [m["content"] for m in memories]

                # 🔥 记忆权重强化（越聊记忆越深刻）
                for m in memories:
                    update_memory_weight(message.user_id, m["id"])

            # 3. RAG 心理学专业知识检索
            if "knowledge_retrieve" in selected_tools:
                knowledge_tool = self.tools.get_tool("knowledge_retrieve")
                message.knowledge = knowledge_tool.run(message)
                logger.info("✅ 已检索心理学/疏导专业知识")
            else:
                message.knowledge = "无"

            # 4. 依恋风格分析
            if message.emotion:
                message = self.attach_agent.run(message)
                logger.info(f"依恋风格：{message.attachment_style}")

            # ============================
            # ✅ 动态对话语气（根据关系等级自动变化）
            # ============================
            dynamic_tone = get_tone_by_user(message.user_id)
            message.strategy = f"{dynamic_tone} | {self.ego.decide_strategy(message.emotion)}"
            logger.info(f"对话策略：{message.strategy}")

            # ============================
            # ✅ 生成最终回复（知识+记忆+策略+语气）
            # ============================
            message = self.response_agent.run(message)
            logger.info(f"最终回复：{message.response}")

            # ============================
            # ✅ 保存记忆 + 自动清理低权重记忆
            # ============================
            save_tool = self.tools.get_tool("save_memory")
            save_tool.run(message)

            # 🔥 自动清理无效记忆（生产级优化）
            auto_clean_low_weight_memory(message.user_id)

            message.status = "completed"
            return message

        except Exception as e:
            logger.error(f"执行异常：{str(e)}", exc_info=True)
            message.status = "error"
            message.response = "我有点累啦，等下再陪你聊～"
            message.emotion = "unknown"
            return message

    # ============================
    # ✅ 流式输出（打字机效果）
    # ============================
    def execute_stream(self, message: AgentMessage):
        """
        流式输出：打字机效果
        完全兼容原有逻辑，只改输出方式
        """
        message = self.execute(message)
        for char in message.response:
            yield char