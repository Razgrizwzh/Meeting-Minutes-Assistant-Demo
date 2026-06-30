"""会议路由：生成纪要 / 历史列表 / 详情。

- POST /api/meetings/generate —— 登录可选；匿名可用但不保存历史
- GET  /api/meetings/history  —— 需登录
- GET  /api/meetings/{id}     —— 需登录
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.api.deps import get_current_user, get_optional_user
from app.schemas.meetings import (
    GenerateResponse,
    MeetingDetail,
    MeetingItem,
    Minutes,
)
from app.services import document_parser, meeting_store, minutes_generator, minutes_renderer

router = APIRouter(prefix="/api/meetings", tags=["meetings"])

# 允许上传的扩展名
_ALLOWED_EXT = {".txt", ".log", ".docx"}


@router.post("/generate", response_model=GenerateResponse)
async def generate_meeting(
    user: dict | None = Depends(get_optional_user),
    text: str | None = Form(None),
    file: UploadFile | None = File(None),
    meeting_name: str | None = Form(None),
    date: str | None = Form(None),
) -> GenerateResponse:
    """生成会议纪要。支持粘贴文本（text）或上传文件（file）。登录则保存历史。"""
    # 1. 获取文本
    transcript = ""
    if file is not None and file.filename:
        suffix = Path(file.filename).suffix.lower()
        if suffix not in _ALLOWED_EXT:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的文件类型: {suffix}，仅支持 .txt/.docx",
            )
        # 写临时文件再用 document_parser 解析（兼容编码检测与 docx）
        content = await file.read()
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        try:
            transcript = document_parser.parse_file(tmp_path)
        finally:
            Path(tmp_path).unlink(missing_ok=True)
    elif text:
        transcript = text

    if not transcript.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="会议文本为空，请粘贴文本或上传文件",
        )

    # 2. 生成结构化纪要
    meta = {"meeting_name": meeting_name, "date": date}
    minutes = minutes_generator.generate_minutes(transcript, meta)
    markdown = minutes_renderer.render_markdown(minutes)

    # 3. 登录用户保存历史
    meeting_id = None
    if user is not None:
        record = meeting_store.save_meeting(user["user_id"], minutes, transcript)
        meeting_id = record["meeting_id"]

    return GenerateResponse(
        meeting_id=meeting_id,
        meeting_name=minutes.get("meeting_name", "未命名会议"),
        date=minutes.get("date", ""),
        minutes=Minutes.model_validate(minutes),
        markdown=markdown,
    )


@router.get("/history", response_model=list[MeetingItem])
def list_history(user: dict = Depends(get_current_user)) -> list[MeetingItem]:
    """登录后返回历史会议列表（按创建时间倒序）。"""
    items = meeting_store.list_meetings(user["user_id"])
    return [MeetingItem(**item) for item in items]


@router.get("/{meeting_id}", response_model=MeetingDetail)
def get_meeting_detail(meeting_id: str, user: dict = Depends(get_current_user)) -> MeetingDetail:
    """取指定会议详情。不存在或非本人则 404。"""
    record = meeting_store.get_meeting(user["user_id"], meeting_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会议不存在")
    markdown = minutes_renderer.render_markdown(record.get("minutes", {}))
    return MeetingDetail(
        meeting_id=record["meeting_id"],
        meeting_name=record.get("meeting_name", "未命名会议"),
        date=record.get("date", ""),
        created_at=record.get("created_at", ""),
        transcript=record.get("transcript", ""),
        minutes=Minutes.model_validate(record.get("minutes", {})),
        markdown=markdown,
    )
