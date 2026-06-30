"""向量存储：ChromaDB 本地持久化 + collection 隔离约定。

【修正点 #4 —— 匿名用户隔离】
原 brief 让所有匿名用户共用单一 ``anonymous`` collection，会导致 A 匿名用户的
会议内容出现在 B 匿名用户的 RAG 回答中（隐私泄露）。

修正后的 collection 命名/隔离约定：
- 登录用户：collection 名为 ``user_{user_id}``，按用户隔离。
- 匿名用户：共用 ``anonymous_pool`` collection，但每个 chunk 的 metadata 带
  ``session_id``，检索时用 ``where={"session_id": session_id}`` 过滤。
  （用 metadata 过滤而非每个 session 建一个 collection，避免 collection 无限增长。）

【分块 / 嵌入 / 检索参数（后续轮实现）】
- 文本分块：RecursiveCharacterTextSplitter，chunk_size=500，overlap=50
- Embedding：langchain-tongyi 的 TongyiEmbeddings（model="text-embedding-v3"，修正点 #2）
- 检索：相似度检索，top_k=4

本轮：仅记录约定，不实现逻辑。
"""

from __future__ import annotations


def get_collection_name(user_id: str | None, session_id: str) -> str:
    """根据登录状态返回 collection 名（约定落地）。

    - user_id 非空（登录）：``user_{user_id}``
    - user_id 为空（匿名）：``anonymous_pool``（检索时按 session_id metadata 过滤）
    """
    raise NotImplementedError("脚手架轮：向量存储未实现，后续 RAG 轮填充")


def add_documents(user_id: str | None, session_id: str, meeting_id: str, texts: list[str]) -> None:
    """向量化文本并入库（含 user_id/session_id/meeting_id metadata）。"""
    raise NotImplementedError("脚手架轮：向量化未实现，后续 RAG 轮填充")


def search(user_id: str | None, session_id: str, query: str, top_k: int = 4) -> list[dict]:
    """相似度检索：优先当前会议，兼顾历史会议。返回带来源信息的文档。"""
    raise NotImplementedError("脚手架轮：检索未实现，后续 RAG 轮填充")
