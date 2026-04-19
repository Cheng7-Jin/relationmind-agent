from agent.base_agent import BaseAgent
from schema.message import AgentMessage
from prompt.response_prompt import RESPONSE_PROMPT
from utils.retry import retry

class ResponseAgent(BaseAgent):
    @retry(max_retries=2)
    def execute(self, message: AgentMessage):
        memory_str = "\n".join(message.retrieved_memories) if message.retrieved_memories else "无"
        knowledge_str = message.knowledge if message.knowledge else "无"
        strategy_str = message.strategy if message.strategy else "倾听"

        # 角色人设（核心）
        role_prompt = message.extra.get("role_prompt", "你是温柔的陪伴者。")

        prompt = RESPONSE_PROMPT.format(
            emotion=message.emotion or "未知",
            attachment_style=message.attachment_style or "未知",
            memory=memory_str,
            user_input=message.user_input,
            knowledge=knowledge_str,
            strategy=strategy_str,
            role_prompt=role_prompt
        )

        message.response = self.llm.invoke(prompt).content.strip()
        return message