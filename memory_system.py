import datetime
import math
from typing import Tuple, List, Dict
from memory.vector_memory import EmotionMemory

# ==============================================
# 关系等级配置（核心业务配置）
# 根据用户记忆数量 → 自动升级关系
# 关系越亲密，AI 召回的记忆越多、语气越温暖
# ==============================================
RELATION_LEVELS = {
    1: {"name": "陌生人", "threshold": 0, "memory_top_k": 2, "tone": "礼貌温和"},
    2: {"name": "熟悉", "threshold": 8, "memory_top_k": 4, "tone": "自然亲切"},
    3: {"name": "亲密", "threshold": 20, "memory_top_k": 6, "tone": "温暖贴心"},
    4: {"name": "挚友", "threshold": 40, "memory_top_k": 8, "tone": "真诚治愈"},
    5: {"name": "灵魂知己", "threshold": 70, "memory_top_k": 10, "tone": "深度陪伴"}
}

# ==============================================
# 【核心方法】获取用户当前关系等级
# 依据：当前用户总记忆条数
# 供：语气控制、记忆检索策略使用
# ==============================================
def get_relation_level(user_id: str) -> Tuple[int, Dict]:
    try:
        mem = EmotionMemory(user_id)
        total_mem = len(mem.db.get()["ids"])
    except:
        total_mem = 0

    # 从最高等级往下匹配，返回符合条件的等级
    for level in sorted(RELATION_LEVELS.keys(), reverse=True):
        if total_mem >= RELATION_LEVELS[level]["threshold"]:
            return level, RELATION_LEVELS[level]
    return 1, RELATION_LEVELS[1]

# ==============================================
# 【核心方法】记忆权重随时间衰减公式
# 时间越久 → 记忆权重越低 → 越容易被遗忘
# ==============================================
def calculate_memory_weight(original_weight: float, create_time: float) -> float:
    hours_passed = (datetime.datetime.now().timestamp() - create_time) / 3600
    decay_factor = math.exp(-0.008 * hours_passed)
    new_weight = original_weight * decay_factor
    return max(new_weight, 0.1)  # 最低不低于0.1，保证记忆不会完全失效

# ==============================================
# 【核心方法】强化记忆（权重+0.2）
# 被检索到的记忆 → 权重提升 → 更不容易被忘记
# ==============================================
def update_memory_weight(user_id: str, memory_id: str, increment: float = 0.2):
    try:
        mem = EmotionMemory(user_id)
        data = mem.db.get(ids=[memory_id])
        if not data["ids"]:
            return
        meta = data["metadatas"][0]
        new_weight = min(meta.get("weight", 1.0) + increment, 2.0)  # 最高2.0
        meta["weight"] = new_weight
        mem.db.update(ids=[memory_id], metadatas=[meta])
    except:
        pass

# ==============================================
# 【核心方法】根据关系等级智能检索记忆
# 1. 获取用户等级
# 2. 动态决定取几条记忆
# 3. 自动过滤低权重记忆
# 4. 自动更新记忆权重
# ==============================================
def retrieve_with_relation(user_id: str, query: str) -> List[dict]:
    level, config = get_relation_level(user_id)
    top_k = config["memory_top_k"]
    mem = EmotionMemory(user_id)

    try:
        docs = mem.db.similarity_search(query, k=top_k, filter={"user_id": user_id})
    except:
        return []

    valid = []
    for doc in docs:
        meta = doc.metadata
        w = meta.get("weight", 1.0)
        t = meta.get("timestamp", 0)
        new_w = calculate_memory_weight(w, t)

        # 权重 >=0.25 才会被AI使用
        if new_w >= 0.25:
            valid.append({
                "id": doc.id,
                "content": doc.page_content,
                "weight": new_w
            })

        # 同步更新数据库中的最新权重
        try:
            meta["weight"] = new_w
            mem.db.update(ids=[doc.id], metadatas=[meta])
        except:
            pass

    # 按权重从高到低排序
    valid.sort(key=lambda x: x["weight"], reverse=True)
    return valid

# ==============================================
# 【核心方法】自动清理低权重记忆
# 权重 < 0.2 → 自动删除
# ==============================================
def auto_clean_low_weight_memory(user_id: str, threshold: float = 0.2):
    try:
        mem = EmotionMemory(user_id)
        data = mem.db.get()
        ids = data["ids"]
        metas = data["metadatas"]
        to_delete = []

        for i, m in enumerate(metas):
            w = m.get("weight", 1.0)
            if w < threshold:
                to_delete.append(ids[i])

        if to_delete:
            mem.db.delete(ids=to_delete)
    except:
        pass

# ==============================================
# 【核心方法】根据用户等级返回AI应使用的语气
# ==============================================
def get_tone_by_user(user_id: str) -> str:
    level, cfg = get_relation_level(user_id)
    return cfg["tone"]

# ==============================================
# 【核心方法】生成记忆摘要（用于情感报告）
# 返回最近8条记忆内容
# ==============================================
def summarize_memory(user_id: str) -> str:
    try:
        mem = EmotionMemory(user_id)
        data = mem.db.get()
        contents = [content for content in data["documents"]]
        if len(contents) == 0:
            return "暂无记忆"
        return "\n".join(contents[-8:])
    except:
        return "暂无记忆"

# ==============================================
# 【扩展备用方法】获取用户全部记忆（完整格式）
# 当前状态：未被调用
# 用途：未来做【查看全部记忆】【记忆管理后台】使用
# 属于业务层方法，不涉及底层数据库细节
# ==============================================
def get_full_memories(user_id: str) -> List[Dict]:
    try:
        mem = EmotionMemory(user_id)
        data = mem.db.get()
        documents = data.get("documents", [])
        metadatas = data.get("metadatas", [])
        ids = data.get("ids", [])

        full_list = []
        for idx, doc in enumerate(documents):
            full_list.append({
                "id": ids[idx],
                "content": doc,
                "metadata": metadatas[idx]
            })
        return full_list
    except:
        return []

# 兼容别名，保证原有调用不报错
retrieve_with_relation = retrieve_with_relation
auto_clean_low_weight_memory = auto_clean_low_weight_memory