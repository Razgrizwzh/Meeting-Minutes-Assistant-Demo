"""纪要渲染：结构化 JSON -> Markdown（brief §4.3 模板）。

"同一 JSON 双渲染"的 Markdown 侧，供前端展示与 .md 导出复用。
不依赖任何 Markdown 解析库，纯字符串拼接。
"""

from __future__ import annotations


def render_markdown(minutes: dict) -> str:
    """把结构化纪要 dict 渲染为 Markdown 字符串。"""
    name = minutes.get("meeting_name", "未命名会议")
    date = minutes.get("date", "")
    attendees = minutes.get("attendees", []) or []
    topics = minutes.get("topics", []) or []
    decisions = minutes.get("decisions", []) or []
    todos = minutes.get("todos", []) or []

    lines: list[str] = []
    lines.append("## 会议纪要\n")
    lines.append(f"**会议名称：** {name}  ")
    lines.append(f"**日期：** {date or '—'}  ")
    lines.append(f"**参会人员：** {'、'.join(attendees) if attendees else '—'}\n")
    lines.append("---\n")

    # 核心议题
    lines.append("### 核心议题与讨论要点\n")
    if topics:
        for i, t in enumerate(topics, 1):
            lines.append(f"{i}. **{t.get('title', '（无标题）')}**")
            for p in t.get("points", []) or []:
                lines.append(f"   - {p}")
            lines.append("")
    else:
        lines.append("（无）\n")

    # 决策结论
    lines.append("### 决策结论\n")
    if decisions:
        for d in decisions:
            owner = d.get("owner", "")
            suffix = f"（负责人：{owner}）" if owner else ""
            lines.append(f"- {d.get('text', '')}{suffix}")
        lines.append("")
    else:
        lines.append("（无）\n")

    # 待办事项
    lines.append("### 待办事项\n")
    if todos:
        lines.append("| 事项 | 负责人 | 截止时间 |")
        lines.append("|------|--------|---------|")
        for td in todos:
            lines.append(
                f"| {td.get('item', '')} | {td.get('owner', '') or '—'} | {td.get('due', '') or '—'} |"
            )
        lines.append("")
    else:
        lines.append("（无）\n")

    return "\n".join(lines).rstrip() + "\n"
