"""对话追问路由：基于 RAG 的多轮问答。

POST /api/chat/query { session_id, question, meeting_id? } -> { answer, sources }
登录可选：登录按 user_id 隔离检索，匿名按 session_id 隔离。
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import get_optional_user
from app.schemas.meetings import ChatResponse, ChatSource
from app.services import rag

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatQueryIn(BaseModel):
    session_id: str
    question: str
    meeting_id: str | None = None


@router.post("/query", response_model=ChatResponse)
def query(body: ChatQueryIn, user: dict | None = Depends(get_optional_user)) -> ChatResponse:
    user_id = user["user_id"] if user is not None else None
    result = rag.answer_query(
        user_id=user_id,
        session_id=body.session_id,
        meeting_id=body.meeting_id,
        question=body.question,
    )
    return ChatResponse(
        answer=result.get("answer", ""),
        sources=[ChatSource(**s) for s in result.get("sources", [])],
    )