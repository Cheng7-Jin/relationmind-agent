from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain.embeddings.base import Embeddings
from langchain_community.embeddings import DashScopeEmbeddings
import datetime
from config.settings import settings

# ==============================================
# 阿里云通义千问 Embedding 模型
# 作用：将文本转为向量，用于向量数据库检索
# ==============================================
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


# ==============================================
# EmotionMemory：向量记忆底层类（数据层）
# 职责：仅负责记忆的 增、查、删、清空
# 不包含任何业务逻辑（权重、等级、策略等全部在 memory_system）
# ==============================================
class EmotionMemory:
    # ==============================================
    # 初始化：每个用户拥有独立的向量库
    # user_id 不同 → 记忆完全隔离
    # ==============================================
    def __init__(self, user_id: str = "default_user"):
        self.user_id = user_id
        self.collection_name = f"memory_{user_id}"

        self.db = Chroma(
            collection_name=self.collection_name,
            embedding_function=AliQwenEmbedding(),
            persist_directory=settings.CHROMA_DIR
        )

    # ==============================================
    # 【核心】保存用户记忆（带情感、依恋类型、时间、权重）
    # ==============================================
    def save_memory(self, user_input, emotion, attachment):
        now = datetime.datetime.now().timestamp()
        doc = Document(
            page_content=f"用户：{user_input}",
            metadata={
                "user_id": self.user_id,
                "emotion": emotion,
                "attachment": attachment,
                "weight": 1.0,
                "timestamp": now
            }
        )
        self.db.add_documents([doc])

    # ==============================================
    # 【核心】根据用户问题检索相关记忆
    # 仅返回当前用户的记忆（多用户隔离）
    # ==============================================
    def retrieve_memory(self, query, top_k=2):
        try:
            docs = self.db.similarity_search(
                query,
                k=top_k,
                filter={"user_id": self.user_id}
            )
            return [d.page_content for d in docs]
        except Exception:
            return []

    # ==============================================
    # 【底层能力】根据ID删除单条记忆
    # 当前状态：未被调用
    # 用途：未来做【手动删除某条记忆】功能时使用
    # ==============================================
    def delete_memory(self, memory_id: str):
        try:
            self.db.delete(ids=[memory_id])
        except Exception:
            pass

    # ==============================================
    # 【核心】清空当前用户的全部记忆
    # 已在 web.py 中被“清空记忆”按钮调用
    # ==============================================
    def clear_memory(self):
        try:
            self.db.delete_collection()
        except Exception:
            pass