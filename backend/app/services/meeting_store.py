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
import os
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
        # 跳过对话持久化文件 {meeting_id}.chat.json，只认会议记录
        if p.name.endswith(".chat.json"):
            continue
        try:
            rec = json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        # 缺 meeting_id 的视为脏文件跳过，避免上层 MeetingItem 校验失败
        if not rec.get("meeting_id"):
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


def _write_atomic(path: Path, record: dict) -> None:
    """原子写：写临时文件再 os.replace，避免并发写损坏。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, path)


def delete_meeting(user_id: str, meeting_id: str) -> bool:
    """删除一条会议记录。存在且已删除返回 True，不存在返回 False。"""
    path = _user_dir(user_id) / f"{meeting_id}.json"
    if not path.exists():
        return False
    try:
        path.unlink()
    except OSError:
        return False
    # 同步清掉相伴的对话文件（若存在）
    chat_path = _user_dir(user_id) / f"{meeting_id}.chat.json"
    chat_path.unlink(missing_ok=True)
    return True


# ---- 对话追问持久化（按会议绑定，仅登录用户落盘） ----
# 对话文件与会议记录同名但加 .chat.json 后缀，独立存放：
#   data/meetings/{user_id}/{meeting_id}.chat.json -> { "messages": [{role, content, sources}] }
# 选独立文件而非往会议 record 里塞，是为了：
#   1) 历史列表/详情读取不被迫加载可能很长的对话；
#   2) 对话高频追加写不会反复重写整个会议 record（含大段 transcript）。

_CHAT_SCHEMA_VERSION = 1


def get_chat(user_id: str, meeting_id: str) -> list[dict]:
    """取某会议的对话记录。无则返回 []。"""
    path = _user_dir(user_id) / f"{meeting_id}.chat.json"
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []
    msgs = data.get("messages") if isinstance(data, dict) else None
    return msgs if isinstance(msgs, list) else []


def append_chat(
    user_id: str,
    meeting_id: str,
    user_msg: dict,
    assistant_msg: dict,
) -> None:
    """追加一轮对话（user + assistant）。meeting 不存在则忽略（防孤儿对话）。

    user_msg / assistant_msg 形如 {role, content, sources?}。
    失败仅记日志不抛——对话持久化失败不应阻断用户拿到回答。
    """
    try:
        path = _user_dir(user_id) / f"{meeting_id}.chat.json"
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                data = {}
        else:
            data = {}
        if not isinstance(data, dict) or "messages" not in data:
            data = {"version": _CHAT_SCHEMA_VERSION, "messages": []}
        data["messages"].append(user_msg)
        data["messages"].append(assistant_msg)
        _write_atomic(path, data)
    except OSError:
        import logging
        logging.getLogger(__name__).warning(
            "对话落盘失败 user_id=%s meeting_id=%s", user_id, meeting_id
        )
