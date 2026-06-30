"""会话历史：内存 session_id -> chat_history 存储（demo 级别，重启清空）。

【修正点 #1 配套】配合 RunnableWithMessageHistory 使用。

- session_id 由前端生成（UUID），存 localStorage
- 每次追问携带最近 5 轮对话历史（trim_messages 截断）
- 重启后清空（demo 级别，不持久化）

本轮：仅记录设计，不实现。
"""

from __future__ import annotations


def get_history(session_id: str) -> list[dict]:
    """取指定 session 的对话历史（最多最近 5 轮）。"""
    raise NotImplementedError("脚手架轮：会话历史未实现，后续轮填充")


def append_history(session_id: str, human: str, ai: str) -> None:
    """追加一轮对话并按最近 5 轮截断。"""
    raise NotImplementedError("脚手架轮：会话历史未实现，后续轮填充")
