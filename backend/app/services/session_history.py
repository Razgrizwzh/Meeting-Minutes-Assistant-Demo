"""会话历史：内存 session_id -> chat_history 存储（demo 级别，重启清空）。

【修正点 #1 配套】配合 LCEL 的历史感知检索使用。保留最近 5 轮（10 条消息）。
"""

from __future__ import annotations

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

_MAX_TURNS = 5  # 保留最近 5 轮 = 10 条消息

_store: dict[str, list[BaseMessage]] = {}


def get_history(session_id: str) -> list[BaseMessage]:
    """取指定 session 的对话历史。"""
    return list(_store.get(session_id, []))


def append_turn(session_id: str, human: str, ai: str) -> None:
    """追加一轮对话并按最近 5 轮截断。"""
    msgs = _store.setdefault(session_id, [])
    msgs.append(HumanMessage(content=human))
    msgs.append(AIMessage(content=ai))
    # 每轮 2 条，保留最近 _MAX_TURNS 轮
    if len(msgs) > _MAX_TURNS * 2:
        _store[session_id] = msgs[-_MAX_TURNS * 2:]


def clear(session_id: str) -> None:
    _store.pop(session_id, None)