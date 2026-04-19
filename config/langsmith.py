import os
from functools import wraps

def setup_langsmith():
    """初始化 LangSmith 全链路追踪"""
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_PROJECT"] = "RelationMind-Agent"

    langchain_api_key = os.getenv("LANGCHAIN_API_KEY")
    if not langchain_api_key:
        raise RuntimeError(
            "环境变量 LANGCHAIN_API_KEY 未设置，请在本地 .env 或系统环境中配置该密钥。"
        )
    os.environ["LANGCHAIN_API_KEY"] = langchain_api_key

    # 如果你希望通过其他方式加载配置，可在这里扩展

def trace_agent(func):
    """给 Agent 核心方法加追踪装饰器（自动追踪全链路）"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        from langchain_core.tracers.context import tracing_v2_enabled
        with tracing_v2_enabled():
            return func(*args, **kwargs)
    return wrapper