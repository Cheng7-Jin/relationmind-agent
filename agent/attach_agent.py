from agent.base_agent import BaseAgent
from schema.message import AgentMessage
from prompt.attach_prompt import ATTACH_PROMPT
from utils.retry import retry

class AttachmentAgent(BaseAgent):
    @retry(max_retries=2)  # 加上重试
    def execute(self, message: AgentMessage):
        prompt = ATTACH_PROMPT.format(text=message.user_input)
        res = self.llm.invoke(prompt).content.strip()
        message.attachment_style = res
        return message