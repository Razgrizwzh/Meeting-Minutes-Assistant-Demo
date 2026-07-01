"""RAG 对话链：基于 LCEL 的多轮检索增强生成。

【修正点 #1 —— 弃用 ConversationalRetrievalChain】
改用 LCEL：
    create_history_aware_retriever + create_retrieval_chain
        + create_stuff_documents_chain
会话历史用 session_history（内存），最近 5 轮。

【调用方式】全走 OpenAI 兼容模式：ChatOpenAI + 百炼兼容 base_url（ChatTongyi 走原生
SDK，业务空间 key 不支持，故弃用）。

【检索策略（brief §4.4）】
- 优先检索当前会议（meeting_id metadata 过滤），匿名按 session_id 隔离
- 回答中引用历史会议内容时，回答末尾附来源会议名 + 日期（由 prompt 引导）
"""

from __future__ import annotations

import logging

from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.services import session_history, vector_store

logger = logging.getLogger(__name__)

# 历史-aware 检索：根据对话历史把追问改写为独立问题
_CONDENSE_PROMPT = ChatPromptTemplate.from_messages([
    ("placeholder", "{chat_history}"),
    ("user", "{input}"),
    ("user",
     "根据上面的对话历史，把用户的最新问题改写为一个可独立检索的查询语句。"
     "若问题已足够独立则原样返回。只输出改写后的查询语句。"),
])

# 问答 prompt：结合检索到的文档回答，并注明来源
_QA_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "你是会议纪要助手的问答助手。根据下面的会议上下文回答用户问题。"
     "如上下文不足以回答，请如实说明。"
     "若引用了某次会议的内容，在回答末尾另起一行以「来源：会议名 · 日期」的形式标注。"
     "\n\n会议上下文：\n{context}"),
    ("placeholder", "{chat_history}"),
    ("user", "{input}"),
])


def _get_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model=settings.chat_model,
        api_key=settings.dashscope_api_key,
        base_url=settings.dashscope_base_url,
        temperature=0.3,
        timeout=120,
    )


def answer_query(
    user_id: str | None,
    session_id: str,
    meeting_id: str | None,
    question: str,
) -> dict:
    """对追问生成带检索上下文的回答。返回 {"answer": str, "sources": list[dict]}。

    sources形如 [{"meeting_name": ..., "date": ...}]（去重）。
    """
    llm = _get_llm()
    retriever = vector_store.as_retriever(user_id, session_id, meeting_id)

    history = session_history.get_history(session_id)

    history_aware_retriever = create_history_aware_retriever(llm, retriever, _CONDENSE_PROMPT)
    qa_chain = create_stuff_documents_chain(llm, _QA_PROMPT)
    retrieval_chain = create_retrieval_chain(history_aware_retriever, qa_chain)

    result = retrieval_chain.invoke({"input": question, "chat_history": history})
    answer: str = result.get("answer", "")
    sources = _extract_sources(result.get("context", []) or [])

    # 记录对话历史
    session_history.append_turn(session_id, question, answer)
    return {"answer": answer, "sources": sources}


def _extract_sources(docs) -> list[dict]:
    """从检索文档 metadata 去重提取来源 [{meeting_name, date}]。"""
    sources: list[dict] = []
    seen = set()
    for doc in docs or []:
        md = doc.metadata or {}
        key = (md.get("meeting_name", ""), md.get("date", ""))
        if key in seen:
            continue
        seen.add(key)
        if any(key):
            sources.append({"meeting_name": key[0], "date": key[1]})
    return sources


async def stream_answer(
    user_id: str | None,
    session_id: str,
    meeting_id: str | None,
    question: str,
):
    """流式版问答：异步生成器，逐 chunk 产出 dict 事件。

    产出顺序：
        {"type": "sources", "sources": [...]}   检索来源（流开始时一次）
        {"type": "token", "content": str}       逐段回答文本
        {"type": "done", "answer": str}         结束，带完整 answer
    异常由调用方捕获（路由层转 SSE error 事件）。
    """
    llm = _get_llm()
    retriever = vector_store.as_retriever(user_id, session_id, meeting_id)
    history = session_history.get_history(session_id)

    # 1. history-aware 改写检索词 + 检索：先拿到 docs 提取 sources
    history_aware_retriever = create_history_aware_retriever(llm, retriever, _CONDENSE_PROMPT)
    # retriever 链以 {input, chat_history} 输入，invoke 返回 {question, context, answer}
    # 这里只取检索结果（context）
    retrieval_result = await history_aware_retriever.ainvoke(
        {"input": question, "chat_history": history}
    )
    # history_aware_retriever 直接返回 docs list
    docs = retrieval_result if isinstance(retrieval_result, list) else retrieval_result.get("context", [])
    sources = _extract_sources(docs)
    yield {"type": "sources", "sources": sources}

    # 2. 用 docs 构造上下文，流式生成回答
    qa_chain = create_stuff_documents_chain(llm, _QA_PROMPT)
    full = []
    async for chunk in qa_chain.astream(
        {"input": question, "chat_history": history, "context": docs}
    ):
        # create_stuff_documents_chain 流式产出的是 str chunk
        text = chunk if isinstance(chunk, str) else str(chunk)
        if text:
            full.append(text)
            yield {"type": "token", "content": text}

    answer = "".join(full)
    # 3. 记录内存对话历史（RAG 检索改写用，最近 5 轮）
    session_history.append_turn(session_id, question, answer)
    yield {"type": "done", "answer": answer}