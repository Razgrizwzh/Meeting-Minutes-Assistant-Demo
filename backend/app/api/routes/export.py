"""导出路由（脚手架轮：stub）。

GET /api/meetings/{id}/export?format=md|docx -> 501。
导出在后续轮实现，数据源为结构化纪要 JSON。
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

router = APIRouter(prefix="/api/meetings", tags=["export"])


@router.get("/{meeting_id}/export")
def export_meeting(meeting_id: str, format: str = "md") -> dict:
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="脚手架轮：导出未实现",
    )
