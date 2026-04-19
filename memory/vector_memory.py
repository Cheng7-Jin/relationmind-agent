from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain.embeddings.base import Embeddings
from langchain_community.embeddings import DashScopeEmbeddings  # 🔥 新增
import numpy as np
from config.settings import settings
import datetime

# ====================== 替换：阿里云通义千问 商用嵌入模型 ======================
class AliQwenEmbedding(Embeddings):
    def __init__(self):
        self.embedding = DashScopeEmbeddings(
            dashscope_api_key=settings.DASHSCOPE_API_KEY,
            model="text-embedding-v1"
        )

    def embed_documents(self, texts):
        return self.embedding.embed_documents(texts)

    def embed_query(self, text):
        return self.embedding.embed_query(text)


class EmotionMemory:
    # ====================== 核心改造：增加 user_id ======================
    def __init__(self, user_id: str = "default_user"):
        self.user_id = user_id  # 每个用户独立ID
        self.collection_name = f"memory_{user_id}"  # 独立集合名

        # 每个用户拥有独立向量库
        self.db = Chroma(
            collection_name=self.collection_name,  # 关键隔离
            embedding_function=AliQwenEmbedding(),  # 🔥 升级：使用阿里千问向量
            persist_directory=settings.CHROMA_DIR
        )

    def save_memory(self, user_input, emotion, attachment):
        now = datetime.datetime.now().timestamp()
        doc = Document(
            page_content=f"用户：{user_input}",
            metadata={
                "user_id": self.user_id,  # 标记归属用户
                "emotion": emotion,
                "attachment": attachment,
                "weight": 1.0,  # ✅ 记忆权重（用于强化/遗忘）
                "timestamp": now  # ✅ 时间戳（用于遗忘机制）
            }
        )
        self.db.add_documents([doc])

    def retrieve_memory(self, query, top_k=2):
        try:
            # 强制只检索当前用户的记忆
            docs = self.db.similarity_search(
                query,
                k=top_k,
                filter={"user_id": self.user_id}  # 隔离核心
            )
            return [d.page_content for d in docs]
        except Exception:
            return []

    # ====================== ✅ 新增：获取完整记忆（带ID、权重、时间） ======================
    def get_full_memories(self, query=None, top_k=10):
        try:
            if query:
                docs = self.db.similarity_search(query, k=top_k, filter={"user_id": self.user_id})
            else:
                docs = self.db.get()
            
            result = []
            for doc in docs:
                result.append({
                    "id": doc.id if hasattr(doc, 'id') else None,
                    "content": doc.page_content,
                    "metadata": doc.metadata
                })
            return result
        except:
            return []

    # ====================== ✅ 新增：更新记忆权重 ======================
    def update_memory_weight(self, memory_id, new_weight):
        try:
            data = self.db.get(ids=[memory_id])
            if not data["ids"]:
                return
            meta = data["metadatas"][0]
            meta["weight"] = new_weight
            self.db.update(ids=[memory_id], metadatas=[meta])
        except:
            pass

    # ====================== ✅ 新增：批量删除低权重记忆 ======================
    def delete_low_weight_memories(self, threshold=0.2):
        try:
            data = self.db.get()
            ids = data["ids"]
            metas = data["metadatas"]
            to_delete = []

            for i, m in enumerate(metas):
                w = m.get("weight", 1.0)
                if w < threshold:
                    to_delete.append(ids[i])

            if to_delete:
                self.db.delete(ids=to_delete)
        except:
            pass

    def clear_memory(self):
        try:
            self.db.delete_collection()
        except Exception:
            pass