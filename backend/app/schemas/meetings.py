"""会议相关 Pydantic 模型（纪要结构、生成请求、历史列表/详情）。"""

from __future__ import annotations

from pydantic import BaseModel


# ---- 纪要结构子模型（对应 brief §4.3）----


class Topic(BaseModel):
    title: str
    points: list[str] = []


class Decision(BaseModel):
    text: str
    owner: str = ""


class Todo(BaseModel):
    item: str
    owner: str = ""
    due: str = ""


class Minutes(BaseModel):
    meeting_name: str
    date: str = ""
    attendees: list[str] = []
    topics: list[Topic] = []
    decisions: list[Decision] = []
    todos: list[Todo] = []


# ---- 生成请求（JSON body 方式）----


class GenerateRequest(BaseModel):
    text: str
    meeting_name: str | None = None
    date: str | None = None


# ---- 响应 ----


class GenerateResponse(BaseModel):
    meeting_id: str | None = None
    meeting_name: str
    date: str = ""
    minutes: Minutes
    markdown: str


class MeetingItem(BaseModel):
    """历史列表项（轻量，不含全文）。"""
    meeting_id: str
    meeting_name: str
    date: str = ""
    created_at: str = ""


class MeetingDetail(BaseModel):
    meeting_id: str
    meeting_name: str
    date: str = ""
    created_at: str = ""
    transcript: str = ""
    minutes: Minutes
    markdown: str


# ---- 对话追问 ----


class ChatSource(BaseModel):
    meeting_name: str = ""
    date: str = ""


class ChatResponse(BaseModel):
    answer: str
    sources: list[ChatSource] = []
