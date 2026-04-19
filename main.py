from langchain_community.chat_models import ChatTongyi
from config.settings import settings
from schema.message import AgentMessage
from memory.vector_memory import EmotionMemory
from agent.emotion_agent import EmotionAgent
from agent.attach_agent import AttachmentAgent
from agent.response_agent import ResponseAgent
from agent.main_agent import MainAgent

# === 初始化 ===
llm = ChatTongyi(
    model_name=settings.MODEL_NAME,
    dashscope_api_key=settings.DASHSCOPE_API_KEY,
    temperature=settings.TEMPERATURE
)

# ==========================================
# 【重要】main.py 仅作为终端入口，使用默认用户
# web 端会自己创建带 user_id 的 memory 传入
# ==========================================
default_user_id = "default_terminal_user"
memory = EmotionMemory(user_id=default_user_id)

# === 子Agent ===
emotion_agent = EmotionAgent(llm)
attach_agent = AttachmentAgent(llm)
response_agent = ResponseAgent(llm)

# === 主Agent ===
main_agent = MainAgent(
    llm=llm,
    memory=memory,
    emotion_agent=emotion_agent,
    attach_agent=attach_agent,
    response_agent=response_agent
)

# === 多轮对话 ===
# ==========================================
# 【仅直接运行时启动终端对话】
# 被 web.py 导入时不执行循环
# ==========================================
if __name__ == "__main__":
    print("=== 企业级 RelationMind Agent ===")
    print("输入 exit 即可退出对话\n")
    while True:
        user_input = input("你：")
        if user_input.lower() == "exit":
            print("Agent：我一直都在，下次见！")
            break

        # 传入 user_id（终端使用默认用户）
        msg = AgentMessage(
            sender="user", 
            receiver="main", 
            user_input=user_input, 
            llm=llm, 
            memory=memory,
            user_id=default_user_id
        )
        result = main_agent.run(msg)

        print(f"\n【情绪】{result.emotion}")
        print(f"【依恋】{result.attachment_style}")
        print(f"【记忆】{result.retrieved_memories}")
        print(f"【执行链路】{' → '.join(result.workflow_trace)}")
        print(f"【总耗时】{result.workflow_duration:.2f}s")
        print(f"【回复】{result.response}\n")
    