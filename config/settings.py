import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # 模型
    DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")
    MODEL_NAME = "qwen-turbo"
    TEMPERATURE = 0.7

    # 重试
    MAX_RETRIES = 2
    RETRY_DELAY = 0.5

    # 记忆
    CHROMA_DIR = "./chroma_db"
    MEMORY_TOP_K = 2

    # 日志
    LOG_LEVEL = "INFO"

settings = Settings()