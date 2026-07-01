"""对话追问路由：基于 RAG 的多轮问答。

POST /api/chat/query { session_id, question, meeting_id? } -> { answer, sources }
GET  /api/chat/{meeting_id}            -> { messages: [...] }   取某会议持久化的对话
登录可选：登录按 user_id 隔离检索，匿名按 session_id 隔离。
对话持久化仅对登录用户、且 meeting_id 属于本人时落盘（按会议绑定）。
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import get_current_user, get_optional_user
from app.schemas.meetings import ChatResponse, ChatSource
from app.services import meeting_store, rag

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatQueryIn(BaseModel):
    session_id: str
    question: str
    meeting_id: str | None = None


class ChatMessageOut(BaseModel):
    role: str
    content: str
    sources: list[ChatSource] = []


class ChatHistoryOut(BaseModel):
    messages: list[ChatMessageOut] = []


@router.post("/query", response_model=ChatResponse)
def query(body: ChatQueryIn, user: dict | None = Depends(get_optional_user)) -> ChatResponse:
    user_id = user["user_id"] if user is not None else None
    result = rag.answer_query(
        user_id=user_id,
        session_id=body.session_id,
        meeting_id=body.meeting_id,
        question=body.question,
    )
    answer = result.get("answer", "")
    sources = [ChatSource(**s) for s in result.get("sources", [])]

    # 登录用户 + 指定了本人的会议 -> 对话落盘（与持久化历史问答回看配套）
    if user_id and body.meeting_id:
        user_msg = {"role": "user", "content": body.question}
        asst_msg = {"role": "assistant", "content": answer, "sources": [s.model_dump() for s in sources]}
        meeting_store.append_chat(user_id, body.meeting_id, user_msg, asst_msg)

    return ChatResponse(answer=answer, sources=sources)


@router.get("/{meeting_id}", response_model=ChatHistoryOut)
def get_chat_history(meeting_id: str, user: dict = Depends(get_current_user)) -> ChatHistoryOut:
    """取指定会议的持久化对话记录（需登录，且会议须属本人）。"""
    # 鉴权：会议不存在或非本人则 404，不泄露是否存在
    if meeting_store.get_meeting(user["user_id"], meeting_id) is None:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会议不存在")
    msgs = meeting_store.get_chat(user["user_id"], meeting_id)
    return ChatHistoryOut(messages=[ChatMessageOut(**m) for m in msgs])