from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid

class AgentMessage(BaseModel):
    # === EGO-MCP 标准字段 ===
    mcp_version: str = "1.0"
    message_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: Optional[str] = None

    user_id: str = "default_user"
    task_id: str = ""
    sender: str = ""
    receiver: str = ""
    user_input: str = ""
    emotion: Optional[str] = None
    attachment_style: Optional[str] = None
    retrieved_memories: List[str] = []
    response: Optional[str] = None
    tools_used: List[str] = []
    status: str = "pending"
    extra: Dict[str, Any] = {}

    # 追踪
    workflow_trace: list[str] = []
    workflow_duration: float = 0.0
    step_results: dict[str, str] = {}

    ego_mcp_prompt: Optional[str] = None

    # ============================
    # ✅ 新增：RAG 知识 + 对话策略
    # ============================
    knowledge: Optional[str] = None
    strategy: Optional[str] = None

    llm: Any = None
    memory: Any = None