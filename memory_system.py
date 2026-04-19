import datetime
import math
from typing import Tuple, List, Dict
from memory.vector_memory import EmotionMemory

RELATION_LEVELS = {
    1: {"name": "陌生人", "threshold": 0, "memory_top_k": 2, "tone": "礼貌温和"},
    2: {"name": "熟悉", "threshold": 8, "memory_top_k": 4, "tone": "自然亲切"},
    3: {"name": "亲密", "threshold": 20, "memory_top_k": 6, "tone": "温暖贴心"},
    4: {"name": "挚友", "threshold": 40, "memory_top_k": 8, "tone": "真诚治愈"},
    5: {"name": "灵魂知己", "threshold": 70, "memory_top_k": 10, "tone": "深度陪伴"}
}

def get_relation_level(user_id: str) -> Tuple[int, Dict]:
    try:
        mem = EmotionMemory(user_id)
        total_mem = len(mem.db.get()["ids"])
    except:
        total_mem = 0

    for level in sorted(RELATION_LEVELS.keys(), reverse=True):
        if total_mem >= RELATION_LEVELS[level]["threshold"]:
            return level, RELATION_LEVELS[level]
    return 1, RELATION_LEVELS[1]

def calculate_memory_weight(original_weight: float, create_time: float) -> float:
    hours_passed = (datetime.datetime.now().timestamp() - create_time) / 3600
    decay_factor = math.exp(-0.008 * hours_passed)
    new_weight = original_weight * decay_factor
    return max(new_weight, 0.1)

def update_memory_weight(user_id: str, memory_id: str, increment: float = 0.2):
    try:
        mem = EmotionMemory(user_id)
        data = mem.db.get(ids=[memory_id])
        if not data["ids"]:
            return
        meta = data["metadatas"][0]
        new_weight = min(meta.get("weight", 1.0) + increment, 2.0)
        meta["weight"] = new_weight
        mem.db.update(ids=[memory_id], metadatas=[meta])
    except:
        pass

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

        if new_w >= 0.25:
            valid.append({
                "id": doc.id,
                "content": doc.page_content,
                "weight": new_w
            })

        try:
            meta["weight"] = new_w
            mem.db.update(ids=[doc.id], metadatas=[meta])
        except:
            pass

    valid.sort(key=lambda x: x["weight"], reverse=True)
    return valid

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

def get_tone_by_user(user_id: str) -> str:
    level, cfg = get_relation_level(user_id)
    return cfg["tone"]

def summarize_memory(user_id: str) -> str:
    try:
        mem = EmotionMemory(user_id)
        data = mem.db.get()
        # 修复：正确读取 documents 字段
        contents = [content for content in data["documents"]]
        if len(contents) == 0:
            return "暂无记忆"
        return "\n".join(contents[-8:])
    except:
        return "暂无记忆"

# 对外别名（保持 main_agent 调用兼容）
retrieve_with_relation = retrieve_with_relation
auto_clean_low_weight_memory = auto_clean_low_weight_memory