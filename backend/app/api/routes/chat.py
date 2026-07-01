"""对话追问路由：基于 RAG 的多轮问答。

POST /api/chat/query         { session_id, question, meeting_id? } -> { answer, sources }  非流式
POST /api/chat/stream        SSE：event=sources/token/done/error，逐 token 输出
GET  /api/chat/{meeting_id}  -> { messages: [...] }   取某会议持久化的对话
登录可选：登录按 user_id 隔离检索，匿名按 session_id 隔离。
对话持久化仅对登录用户、且 meeting_id 属于本人时落盘（按会议绑定）。
"""

from __future__ import annotations

import json

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
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

    # 登录用户 + 指定了本人的会议 -> 对话落盘
    if user_id and body.meeting_id:
        user_msg = {"role": "user", "content": body.question}
        asst_msg = {"role": "assistant", "content": answer, "sources": [s.model_dump() for s in sources]}
        meeting_store.append_chat(user_id, body.meeting_id, user_msg, asst_msg)

    return ChatResponse(answer=answer, sources=sources)


def _sse(event: str, data: dict) -> str:
    """构造一条 SSE 消息。data 序列化为 JSON。"""
    payload = json.dumps(data, ensure_ascii=False)
    return f"event: {event}\ndata: {payload}\n\n"


@router.post("/stream")
async def stream(body: ChatQueryIn, user: dict | None = Depends(get_optional_user)):
    """SSE 流式问答。逐 token 推送回答，结束后落盘对话（登录用户）。"""
    user_id = user["user_id"] if user is not None else None
    question = body.question
    meeting_id = body.meeting_id

    async def gen():
        answer_acc: list[str] = []
        sources_sent: list[dict] = []
        err_msg: str | None = None
        try:
            async for ev in rag.stream_answer(
                user_id=user_id,
                session_id=body.session_id,
                meeting_id=meeting_id,
                question=question,
            ):
                etype = ev.get("type")
                if etype == "sources":
                    sources_sent = ev.get("sources", [])
                    yield _sse("sources", {"sources": sources_sent})
                elif etype == "token":
                    piece = ev.get("content", "")
                    answer_acc.append(piece)
                    yield _sse("token", {"content": piece})
                elif etype == "done":
                    final_answer = ev.get("answer", "") or "".join(answer_acc)
                    # 登录用户 + 本人会议 -> 落盘完整对话
                    if user_id and meeting_id:
                        try:
                            user_msg = {"role": "user", "content": question}
                            asst_msg = {
                                "role": "assistant",
                                "content": final_answer,
                                "sources": sources_sent,
                            }
                            meeting_store.append_chat(user_id, meeting_id, user_msg, asst_msg)
                        except Exception:
                            import logging
                            logging.getLogger(__name__).exception("对话落盘失败 meeting_id=%s", meeting_id)
                    yield _sse("done", {"answer": final_answer, "sources": sources_sent})
                    return
        except Exception as e:
            import logging
            logging.getLogger(__name__).exception("SSE 流式问答失败")
            err_msg = "追问失败，请重试"
            yield _sse("error", {"message": err_msg})

    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # 关闭 nginx/代理缓冲，确保逐块下发
        },
    )


@router.get("/{meeting_id}", response_model=ChatHistoryOut)
def get_chat_history(meeting_id: str, user: dict = Depends(get_current_user)) -> ChatHistoryOut:
    """取指定会议的持久化对话记录（需登录，且会议须属本人）。"""
    if meeting_store.get_meeting(user["user_id"], meeting_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会议不存在")
    msgs = meeting_store.get_chat(user["user_id"], meeting_id)
    return ChatHistoryOut(messages=[ChatMessageOut(**m) for m in msgs])