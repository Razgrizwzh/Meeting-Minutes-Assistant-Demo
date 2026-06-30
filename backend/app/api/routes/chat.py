"""对话追问路由（脚手架轮：stub）。

POST /api/chat/query -> 501。完整 RAG 链在后续轮实现。
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatQueryIn(BaseModel):
    session_id: str
    question: str
    meeting_id: str | None = None


@router.post("/query")
def query(body: ChatQueryIn) -> dict:
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="脚手架轮：RAG 追问未实现",
    )
