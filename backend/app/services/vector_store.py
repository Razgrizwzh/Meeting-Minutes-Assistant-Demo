"""向量存储：ChromaDB 本地持久化 + OpenAIEmbeddings（百炼兼容端点）。

【修正点 #4 —— 匿名用户隔离】
- 登录用户：collection 名 ``user_{user_id}``，按用户隔离。
- 匿名用户：共用 ``anonymous_pool`` collection，每个 chunk metadata 带 ``session_id``，
  检索时用 ``filter={"session_id": session_id}`` 过滤（langchain Chroma 封装的过滤键名为
  ``filter``，不是 Chroma 原生的 ``where``）。

【修正点 #2 —— 走 OpenAI 兼容模式】
业务空间专属 key 只支持兼容端点，故用 langchain-openai 的 OpenAIEmbeddings，
base_url 指向百炼兼容端点，model=text-embedding-v3，dimensions=1024。

【分块 / 检索参数】
- RecursiveCharacterTextSplitter，chunk_size=500，overlap=50
- 相似度检索，top_k=4
"""

from __future__ import annotations

import logging
from pathlib import Path

from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter

from app.core.config import settings

logger = logging.getLogger(__name__)

_EMBED_DIMENSIONS = 1024
_TOP_K = 4
_CHUNK_SIZE = 500
_CHUNK_OVERLAP = 50

# 复用 embedding 实例（client 单例）
_embeddings: OpenAIEmbeddings | None = None
_splitter: RecursiveCharacterTextSplitter | None = None


def _get_embeddings() -> OpenAIEmbeddings:
    global _embeddings
    if _embeddings is None:
        _embeddings = OpenAIEmbeddings(
            model=settings.embedding_model,
            api_key=settings.dashscope_api_key,
            base_url=settings.dashscope_base_url,
            dimensions=_EMBED_DIMENSIONS,
            check_embedding_ctx_length=False,  # 百炼 v3 不走 tiktoken 计数
        )
    return _embeddings


def _get_splitter() -> RecursiveCharacterTextSplitter:
    global _splitter
    if _splitter is None:
        _splitter = RecursiveCharacterTextSplitter(
            chunk_size=_CHUNK_SIZE, chunk_overlap=_CHUNK_OVERLAP
        )
    return _splitter


def collection_name(user_id: str | None) -> str:
    """登录用户 ``user_{user_id}``；匿名用户 ``anonymous_pool``。"""
    return f"user_{user_id}" if user_id else "anonymous_pool"


def _persist_dir() -> str:
    Path(settings.chroma_db_path).mkdir(parents=True, exist_ok=True)
    return settings.chroma_db_path


def _metadata_for(user_id: str | None, session_id: str, meeting_id: str,
                  meeting_name: str, date: str) -> dict:
    return {
        "user_id": user_id or "",
        "session_id": session_id or "",
        "meeting_id": meeting_id,
        "meeting_name": meeting_name or "",
        "date": date or "",
    }


def add_documents(
    user_id: str | None,
    session_id: str,
    meeting_id: str,
    text: str,
    meeting_name: str = "",
    date: str = "",
) -> int:
    """分块 + 嵌入 + 入库。返回入库的 chunk 数。可能抛异常（调用方处理）。"""
    if not text.strip():
        return 0

    splitter = _get_splitter()
    chunks = splitter.split_text(text)
    if not chunks:
        return 0

    metadatas = [
        _metadata_for(user_id, session_id, meeting_id, meeting_name, date)
        for _ in chunks
    ]

    vs = Chroma.from_texts(
        texts=chunks,
        embedding=_get_embeddings(),
        metadatas=metadatas,
        collection_name=collection_name(user_id),
        persist_directory=_persist_dir(),
    )
    logger.info("向量化入库: %s 个 chunk -> collection=%s meeting_id=%s",
                len(chunks), collection_name(user_id), meeting_id)
    return len(chunks)


def as_retriever(user_id: str | None, session_id: str, meeting_id: str | None = None):
    """构造 retriever。登录优先当前会议；匿名按 session_id 过滤所有 chunks。

    无 meeting_id 时检索该 collection 下该用户/session 的全部 chunk。
    """
    vs = Chroma(
        embedding_function=_get_embeddings(),
        collection_name=collection_name(user_id),
        persist_directory=_persist_dir(),
    )

    filter_dict: dict = {}
    if user_id and meeting_id:
        # 登录用户：优先当前会议
        filter_dict = {"meeting_id": meeting_id}
    elif not user_id:
        # 匿名：按 session_id 隔离
        filter_dict = {"session_id": session_id or ""}

    search_kwargs: dict = {"k": _TOP_K}
    if filter_dict:
        search_kwargs["filter"] = filter_dict
    return vs.as_retriever(search_kwargs=search_kwargs)


# 兼容旧骨架里暴露的 search 函数（供轻量调试/兜底使用）
def search(user_id: str | None, session_id: str, query: str,
            meeting_id: str | None = None, top_k: int = _TOP_K) -> list[dict]:
    """相似度检索，返回 [{text, metadata}]。"""
    from langchain_community.vectorstores import Chroma as _C
    vs = _C(
        embedding_function=_get_embeddings(),
        collection_name=collection_name(user_id),
        persist_directory=_persist_dir(),
    )
    filter_dict: dict = {"user_id": user_id or ""} if user_id else {"session_id": session_id or ""}
    docs = vs.similarity_search(query, k=top_k, filter=filter_dict)
    return [{"text": d.page_content, "metadata": d.metadata} for d in docs]