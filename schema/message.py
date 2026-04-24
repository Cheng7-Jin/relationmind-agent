from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid

class AgentMessage(BaseModel):
    # === EGO-MCP 协议标准字段（项目核心协议）===
    mcp_version: str = "1.0"                # 在用 → 协议版本
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))  # 在用 → 唯一消息ID
    session_id: Optional[str] = None         # 在用 → 会话区分

    user_id: str = "default_user"           # 核心在用 → 用户隔离
    task_id: str = ""                       # 备用 → 未来任务系统
    sender: str = ""                        # 在用 → 发送者标识
    receiver: str = ""                      # 在用 → 接收者标识
    user_input: str = ""                    # 核心在用 → 用户输入
    emotion: Optional[str] = None            # 核心在用 → 情绪识别
    attachment_style: Optional[str] = None  # 核心在用 → 依恋风格
    retrieved_memories: List[str] = []      # 核心在用 → 记忆检索结果
    response: Optional[str] = None          # 核心在用 → AI回复
    tools_used: List[str] = []              # 在用 → 工具调用记录
    status: str = "pending"                 # 在用 → 状态流转
    extra: Dict[str, Any] = {}              # 备用 → 扩展字段

    # 追踪日志
    workflow_trace: list[str] = []          # 在用 → 工作流追踪
    workflow_duration: float = 0.0          # 在用 → 耗时统计
    step_results: dict[str, str] = {}       # 在用 → 步骤结果

    ego_mcp_prompt: Optional[str] = None    # 核心在用 → 你的专属心智提示词

    # 知识 + 策略
    knowledge: Optional[str] = None         # 在用 → RAG 外部知识
    strategy: Optional[str] = None          # 在用 → 对话策略（语气/等级）

    llm: Any = None                         # 在用 → 大模型实例
    memory: Any = None                      # 在用 → 记忆实例