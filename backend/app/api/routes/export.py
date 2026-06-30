"""导出路由：导出指定会议纪要。

GET /api/meetings/{id}/export?format=md|docx
- md：复用 minutes_renderer.render_markdown，返回 text/markdown 附件
- docx：由结构化 JSON 经 docx_exporter 渲染，返回 .docx 附件
需登录，且只能导出本人会议。
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse, PlainTextResponse
from urllib.parse import quote

from app.api.deps import get_current_user
from app.services import docx_exporter, meeting_store, minutes_renderer
from app.services.minutes_renderer import render_markdown

router = APIRouter(prefix="/api/meetings", tags=["export"])

_FORMATS = {"md", "docx"}


def _safe_filename(name: str, ext: str) -> str:
    base = "".join(c for c in (name or "会议纪要") if c not in '\\/:*?"<>|').strip() or "会议纪要"
    return f"{base}.{ext}"


@router.get("/{meeting_id}/export")
def export_meeting(meeting_id: str, format: str = "md",
                    user: dict = Depends(get_current_user)):
    if format not in _FORMATS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"不支持的格式: {format}，仅支持 md/docx")

    record = meeting_store.get_meeting(user["user_id"], meeting_id)
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会议不存在")

    minutes = record.get("minutes", {})
    name = record.get("meeting_name", "会议纪要")
    filename = _safe_filename(name, "md" if format == "md" else "docx")
    quoted = quote(filename)  # 处理中文文件名

    if format == "md":
        md_text = render_markdown(minutes)
        return PlainTextResponse(
            content=md_text,
            media_type="text/markdown; charset=utf-8",
            headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quoted}"},
        )

    # docx
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".docx")
    tmp.close()
    docx_exporter.render_docx(minutes, tmp.name)
    return FileResponse(
        path=tmp.name,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=filename,
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quoted}"},
    )