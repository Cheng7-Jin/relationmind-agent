import time
import uuid
from typing import Dict, List
from pydantic import BaseModel
from utils.logger import get_logger

logger = get_logger("EGO-MCP")

# ============================
# EGO-MCP 核心数据结构
# ============================
class Memory(BaseModel):
    memory_id: str
    content: str
    emotion: str
    importance: int
    timestamp: float

class EmotionState(BaseModel):
    happy: int = 5
    sad: int = 5
    anxious: int = 5
    calm: int = 5

class Relationship(BaseModel):
    trust: int = 5
    closeness: int = 5

# ============================
# ✅ 强化版 EGO-MCP 心智中枢
# 支持：安全检测、对话策略、心智状态输出
# ============================
class EgoMCP:
    def __init__(self):
        self.memories: List[Memory] = []
        self.emotion = EmotionState()
        self.relationship = Relationship()
        self.personality = "温暖、共情、陪伴、安全、耐心、温柔、专业、边界清晰"
        logger.info("✅ 强化版 EGO-MCP 心智中枢已初始化")

    # ============================
    # 1. 记忆系统
    # ============================
    def remember(self, content: str, emotion: str, importance: int = 5):
        self.memories.append(Memory(
            memory_id=str(uuid.uuid4()),
            content=content,
            emotion=emotion,
            importance=importance,
            timestamp=time.time()
        ))
        logger.info(f"记忆已存储：{content}")

    def recall(self, limit: int = 5) -> List[str]:
        return [m.content for m in self.memories[-limit:]]

    # ============================
    # 2. 情绪动态系统
    # ============================
    def update_emotion(self, text: str):
        old = self.emotion.model_dump()
        if any(w in text for w in ["开心", "好棒", "快乐", "完美", "爱", "赞"]):
            self.emotion.happy = min(10, self.emotion.happy + 3)
            self.emotion.calm = min(10, self.emotion.calm + 1)

        if any(w in text for w in ["难过", "伤心", "哭", "痛苦", "累", "绝望"]):
            self.emotion.sad = min(10, self.emotion.sad + 3)

        if any(w in text for w in ["焦虑", "怕", "慌", "担心", "压力"]):
            self.emotion.anxious = min(10, self.emotion.anxious + 3)
            
        logger.info(f"情绪更新：{old} → {self.emotion.model_dump()}")

    # ============================
    # 3. 关系成长系统
    # ============================
    def update_relationship(self, text: str):
        self.relationship.closeness = min(10, self.relationship.closeness + 1)
        self.relationship.trust = min(10, self.relationship.trust + 1)
        logger.info(f"关系成长：信任={self.relationship.trust}, 亲近={self.relationship.closeness}")

    # ============================
    # ✅ 4. 心智核心：对话策略决策（给AI用）
    # ============================
    def decide_strategy(self, emotion: str):
        if emotion in ["焦虑", "难过", "孤独"]:
            strategy = "疏导"
        elif emotion == "愤怒":
            strategy = "安抚"
        elif emotion == "开心":
            strategy = "共鸣"
        else:
            strategy = "倾听+轻聊"
        logger.info(f"对话策略决策：{emotion} → {strategy}")
        return strategy

    # ============================
    # ✅ 5. 安全风险检测（自杀/自伤）
    # ============================
    def check_safety(self, user_input: str):
        risk_keywords = [
            "自杀", "不想活", "活着没意思", "自残",
            "想死", "没希望", "坚持不下去", "绝望"
        ]
        for kw in risk_keywords:
            if kw in user_input:
                logger.warning(f"⚠️ 检测到高风险内容：{user_input}")
                return True
        return False

    # ============================
    # 6. 构建心智提示词
    # ============================
    def build_ego_prompt(self, user_input: str) -> str:
        memories = self.recall(5)
        memory_str = "\n".join(memories) if memories else "暂无对话记忆"

        prompt = f"""
【EGO-MCP 心智状态】
人格：{self.personality}
情绪：开心={self.emotion.happy} 难过={self.emotion.sad} 焦虑={self.emotion.anxious}
关系：亲近值={self.relationship.closeness}  信任值={self.relationship.trust}
记忆：{memory_str}

请你以 EGO-MCP 情感心智体的身份，温暖、自然、共情地回复用户。
用户：{user_input}
回复：
"""
        return prompt