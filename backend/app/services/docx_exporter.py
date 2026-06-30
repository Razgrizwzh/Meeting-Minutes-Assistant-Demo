"""docx 导出：由结构化纪要 JSON 渲染 Word 文档。

【修正点 #3 —— 不解析 Markdown】
导出 docx 的数据源是 minutes_generator 返回的**结构化 JSON**，而非 Markdown 文本。
python-docx 作为底层 OOXML 构建器（add_heading / add_paragraph / add_table），
直接按 JSON 字段渲染，无需任何 Markdown 解析。

兜底方案：若上游只有 Markdown（非预期路径），针对固定模板手写 md->docx 映射。

本轮：仅记录设计，不实现。
"""

from __future__ import annotations

from pathlib import Path


def render_docx(minutes: dict, output_path: str | Path) -> Path:
    """将结构化纪要 JSON 渲染为 .docx，写入 output_path 并返回该路径。

    minutes 结构见 minutes_generator.py 注释。
    """
    raise NotImplementedError("脚手架轮：docx 导出未实现，后续轮填充")
