"""RAG 对话链：基于 LCEL 的多轮检索增强生成。

【修正点 #1 —— 弃用 ConversationalRetrievalChain】
该类已从 langchain 核心移入 langchain_community 并标记弃用。本项目改用 LCEL：

    create_history_aware_retriever + create_retrieval_chain
        + create_stuff_documents_chain + RunnableWithMessageHistory

- 会话历史：RunnableWithMessageHistory + 内存 BaseStore（session_history.py）
- 最近 5 轮：用 trim_messages 截断，避免上下文膨胀

【检索策略（brief §4.4，后续轮实现）】
- 优先检索当前会议（meeting_id metadata 过滤）
- 兼顾该用户的历史会议纪要
- 回答中如引用历史会议内容，注明来源会议名称与日期

【Embedding / LLM】
- Embedding：TongyiEmbeddings（text-embedding-v3）
- Chat：ChatTongyi（qwen-plus）；或纪要生成复用 openai 兼容 client

本轮：仅记录设计，不实现。
"""

from __future__ import annotations


def answer_query(
    user_id: str | None,
    session_id: str,
    meeting_id: str | None,
    question: str,
) -> dict:
    """对追问生成带检索上下文的回答。

    返回示例：{"answer": "...", "sources": [{"meeting_name": ..., "date": ...}]}
    """
    raise NotImplementedError("脚手架轮：RAG 链未实现，后续轮填充")
