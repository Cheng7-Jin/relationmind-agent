from langchain_chroma import Chroma
from langchain_community.embeddings import FakeEmbeddings
import os
from tools.base_tool import BaseTool
from schema.message import AgentMessage
from utils.logger import get_logger

logger = get_logger("KnowledgeTool")

class KnowledgeRetrieveTool(BaseTool):
    name = "knowledge_retrieve"
    description = "从心理学、情感疏导、依恋理论、聊天技巧知识库中检索专业知识，用于更科学地回答用户"

    def __init__(self):
        self.embedding = FakeEmbeddings(size=128)
        self.db = Chroma(
            collection_name="psychology_knowledge",
            embedding_function=self.embedding,
            persist_directory="./chroma_knowledge"
        )

    def _load_knowledge(self):
        try:
            # 自动加载 knowledge 目录下的所有文档
            files = [
                "knowledge/emotion_skills.md",
                "knowledge/attachment_guide.md",
                "knowledge/communication_skills.md",
                "knowledge/safety_rules.md"
            ]

            docs = []
            for f_path in files:
                if os.path.exists(f_path):
                    with open(f_path, "r", encoding="utf-8") as f:
                        content = f.read()
                        docs.append(content)

            # 存入向量库
            if docs:
                self.db.add_texts(docs)
                logger.info(f"✅ 专业知识库加载成功，共 {len(docs)} 条文档")
        except Exception as e:
            logger.error(f"❌ 知识库加载失败: {e}", exc_info=True)

    def run(self, message: AgentMessage) -> str:
        try:
            query = message.user_input

            # 首次运行自动初始化知识库
            if not self.db.get()["ids"]:
                self._load_knowledge()

            # 检索最相关3条
            results = self.db.similarity_search(query, k=3)
            content = "\n---\n".join([r.page_content for r in results])
            logger.info(f"✅ 知识检索完成，关键词: {query[:30]}，结果长度: {len(content)}")
            return content
        except Exception as e:
            logger.error(f"❌ 知识检索失败: {e}", exc_info=True)
            return ""