"""纪要生成：调用 qwen3.7-plus（OpenAI 兼容模式）生成结构化会议纪要 JSON。

【修正点 #3 —— 避免解析 Markdown】
LLM 返回**结构化 JSON**（匹配 brief §4.3 固定模板），再由 minutes_renderer 渲染
Markdown、由 docx_exporter 渲染 docx，从根本上回避 Markdown 解析。

【调用方式】
业务空间专属 key 只支持 OpenAI 兼容端点（见 test/README.md），故用
langchain-openai 的 ChatOpenAI，base_url 指向百炼兼容端点，
response_format 强制 JSON 输出，温度调低提升结构稳定性。

返回结构：
    {
        "meeting_name": "...",
        "date": "2025-xx-xx",
        "attendees": ["张三", ...],
        "topics": [{"title": "...", "points": ["...", ...]}, ...],
        "decisions": [{"text": "...", "owner": "张三"}, ...],
        "todos": [{"item": "...", "owner": "张三", "due": "2025-xx"}, ...]
    }
"""

from __future__ import annotations

import json
import logging

from langchain_openai import ChatOpenAI

from app.core.config import settings

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """你是会议纪要助手。请根据给定的会议转写文本，生成结构化的会议纪要。

严格输出 JSON，不要输出任何 Markdown 代码块标记或多余文字。JSON schema：
{
  "meeting_name": "会议名称（字符串；若未提供则从转写内容推断，无则填'未命名会议'）",
  "date": "会议日期 YYYY-MM-DD（若未提供则填空字符串）",
  "attendees": ["参会人员姓名列表"],
  "topics": [
    {"title": "议题标题", "points": ["讨论要点1", "讨论要点2"]}
  ],
  "decisions": [
    {"text": "决策结论", "owner": "负责人姓名（可空字符串）"}
  ],
  "todos": [
    {"item": "待办事项", "owner": "负责人姓名（可空字符串）", "due": "截止时间 YYYY-MM 或 YYYY-MM-DD（可空字符串）"}
  ]
}
要求：
- 字段必须齐全（无内容时用空数组或空字符串）。
- 议题、决策、待办从转写内容提炼，保持简洁准确。
- 若提供了 meeting_name / date，优先采用提供的值。
"""


def _get_llm() -> ChatOpenAI:
    """构建 ChatOpenAI 实例（OpenAI 兼容模式连百炼）。"""
    return ChatOpenAI(
        model=settings.chat_model,
        api_key=settings.dashscope_api_key,
        base_url=settings.dashscope_base_url,
        temperature=0.2,
        model_kwargs={"response_format": {"type": "json_object"}},
        timeout=120,  # 长文本生成可能 60-90 秒，放宽到 120s
    )


def _normalize(data: dict, meta: dict) -> dict:
    """校验并补齐字段，确保结构稳定。"""
    def as_str(v):
        return v if isinstance(v, str) else (str(v) if v is not None else "")

    def as_list(v):
        return v if isinstance(v, list) else []

    # meeting_name/date 优先用 meta 提供的
    name = as_str(meta.get("meeting_name")) or as_str(data.get("meeting_name")) or "未命名会议"
    date = as_str(meta.get("date")) or as_str(data.get("date"))

    attendees = [a for a in as_list(data.get("attendees")) if isinstance(a, str) and a.strip()]

    topics = []
    for t in as_list(data.get("topics")):
        if not isinstance(t, dict):
            continue
        topics.append({
            "title": as_str(t.get("title")) or "（无标题）",
            "points": [p for p in as_list(t.get("points")) if isinstance(p, str) and p.strip()],
        })

    decisions = []
    for d in as_list(data.get("decisions")):
        if not isinstance(d, dict):
            continue
        decisions.append({"text": as_str(d.get("text")), "owner": as_str(d.get("owner"))})

    todos = []
    for td in as_list(data.get("todos")):
        if not isinstance(td, dict):
            continue
        todos.append({
            "item": as_str(td.get("item")),
            "owner": as_str(td.get("owner")),
            "due": as_str(td.get("due")),
        })

    return {
        "meeting_name": name,
        "date": date,
        "attendees": attendees,
        "topics": topics,
        "decisions": decisions,
        "todos": todos,
    }


def generate_minutes(transcript: str, meta: dict | None = None) -> dict:
    """由会议转写文本生成结构化纪要 JSON。

    meta 可含 meeting_name、date。返回规范化后的纪要 dict。
    LLM 返回非 JSON 时做兜底，返回带 error 标记的最小结构，不抛异常。
    """
    meta = meta or {}
    llm = _get_llm()

    user_hint = ""
    if meta.get("meeting_name"):
        user_hint += f"会议名称：{meta['meeting_name']}\n"
    if meta.get("date"):
        user_hint += f"会议日期：{meta['date']}\n"
    user_hint += f"会议转写文本：\n{transcript}"

    messages = [
        ("system", _SYSTEM_PROMPT),
        ("user", user_hint),
    ]

    try:
        resp = llm.invoke(messages)
        content = resp.content if isinstance(resp.content, str) else str(resp.content)
        data = json.loads(content)
    except json.JSONDecodeError as e:
        logger.warning("LLM 返回非合法 JSON：%s", e)
        return _normalize({}, meta) | {"_error": "LLM 返回内容无法解析为 JSON"}
    except Exception as e:
        logger.exception("纪要生成调用失败")
        raise

    return _normalize(data, meta)
