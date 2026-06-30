"""历史会议元数据持久化：data/meetings/{user_id}/{meeting_id}.json（登录用户）。

每条记录 schema：
    {
        "meeting_id": "uuid4",
        "meeting_name": "...",
        "date": "YYYY-MM-DD",
        "created_at": "ISO-8601",
        "transcript": "原始转写文本",
        "minutes": {...}   # 结构化纪要 JSON
    }

匿名用户不落库（brief §4.1：未登录不保存历史）。
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from app.core.config import settings


def _user_dir(user_id: str) -> Path:
    return Path(settings.meetings_data_path) / user_id


def save_meeting(
    user_id: str,
    minutes: dict,
    transcript: str,
) -> dict:
    """保存一条会议记录，返回完整记录 dict（含 meeting_id）。"""
    meeting_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    record = {
        "meeting_id": meeting_id,
        "meeting_name": minutes.get("meeting_name", "未命名会议"),
        "date": minutes.get("date", ""),
        "created_at": now,
        "transcript": transcript,
        "minutes": minutes,
    }

    d = _user_dir(user_id)
    d.mkdir(parents=True, exist_ok=True)
    path = d / f"{meeting_id}.json"
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    return record


def list_meetings(user_id: str) -> list[dict]:
    """列该用户历史会议，按 created_at 倒序。返回轻量元数据（不含全文）。"""
    d = _user_dir(user_id)
    if not d.exists():
        return []
    items: list[dict] = []
    for p in d.glob("*.json"):
        try:
            rec = json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        items.append({
            "meeting_id": rec.get("meeting_id"),
            "meeting_name": rec.get("meeting_name", "未命名会议"),
            "date": rec.get("date", ""),
            "created_at": rec.get("created_at", ""),
        })
    items.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return items


def get_meeting(user_id: str, meeting_id: str) -> dict | None:
    """取完整会议详情。不存在返回 None。"""
    path = _user_dir(user_id) / f"{meeting_id}.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def delete_meeting(user_id: str, meeting_id: str) -> bool:
    """删除一条会议记录。存在且已删除返回 True，不存在返回 False。"""
    path = _user_dir(user_id) / f"{meeting_id}.json"
    if not path.exists():
        return False
    try:
        path.unlink()
    except OSError:
        return False
    return True
