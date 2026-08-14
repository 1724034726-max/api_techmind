# 写作助手：调用方舟 LLM，按任务解析结构化结果
from __future__ import annotations

import json
import re
from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

from app.core.error_codes import ErrorCode
from app.core.exceptions import exception
from app.integrations.ark import ark_chat
from app.schemas.editor_ai import (
    ExpandDTO,
    ExpandVO,
    OpeningDTO,
    OpeningVO,
    SummaryDTO,
    SummaryVO,
    TopicAnalyzeDTO,
    TopicAnalyzeVO,
)

T = TypeVar("T", bound=BaseModel)

_JSON_BLOCK = re.compile(r"```(?:json)?\s*([\s\S]*?)```", re.IGNORECASE)


def _extract_json_text(raw: str) -> str:
    """从模型输出中抽出 JSON 对象文本。"""
    text = (raw or "").strip()
    if not text:
        raise exception(ErrorCode.ERR_AI_BAD_RESPONSE)
    m = _JSON_BLOCK.search(text)
    if m:
        text = m.group(1).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        raise exception(ErrorCode.ERR_AI_BAD_RESPONSE)
    return text[start : end + 1]


def _parse_vo(raw: str, model: type[T]) -> T:
    """解析并校验为指定 VO。"""
    try:
        obj: Any = json.loads(_extract_json_text(raw))
        return model.model_validate(obj)
    except (json.JSONDecodeError, ValidationError) as exc:
        raise exception(ErrorCode.ERR_AI_BAD_RESPONSE, detail=str(exc)) from exc


def analyze_topic(payload: TopicAnalyzeDTO) -> TopicAnalyzeVO:
    # 选题：切口 + 大纲骨架
    system = (
        "你是 TechMind 技术社区的选题助手。"
        "根据关键词给出竞争洞察与 3 个差异化写作切口。"
        "禁止只堆砌标题文案；每个切口要有 angle、可落地的工作标题、简短竞争提示、Markdown 大纲。"
        "只输出一个 JSON 对象，不要 Markdown 说明："
        '{"insight":"string","angles":[{"angle":"string","title":"string","hint":"string","outline_md":"string"}]}'
    )
    user = f"关键词：{payload.keyword.strip()}"
    raw = ark_chat(user, system_prompt=system, temperature=0.3)
    return _parse_vo(raw, TopicAnalyzeVO)


def expand_draft(payload: ExpandDTO) -> ExpandVO:
    # 扩写：只返回可追加的 Markdown
    system = (
        "你是技术文章扩写助手。根据标题与现有 Markdown 正文（多为大纲），"
        "生成一段可追加到文末的初稿 Markdown，不要重复已有内容，不要输出全文替换。"
        '只输出 JSON：{"appendix_md":"string"}'
    )
    user = (
        f"标题：{payload.title.strip() or '（无标题）'}\n\n"
        f"现有正文：\n{(payload.content_md or '').strip() or '（空，请写一篇可落地的初稿骨架）'}"
    )
    raw = ark_chat(user, system_prompt=system, temperature=0.4)
    return _parse_vo(raw, ExpandVO)


def polish_summary(payload: SummaryDTO) -> SummaryVO:
    # 润色：导读候选
    system = (
        "你是技术文章导读助手。根据标题与正文，生成 3 条一句话导读摘要，"
        "说明本文解决什么问题，语气专业克制，每条不超过 60 字。"
        '只输出 JSON：{"candidates":[{"label":"string","text":"string"}]}'
    )
    user = (
        f"标题：{payload.title.strip() or '（无标题）'}\n\n"
        f"正文：\n{(payload.content_md or '')[:6000]}"
    )
    raw = ark_chat(user, system_prompt=system, temperature=0.3)
    return _parse_vo(raw, SummaryVO)


def polish_opening(payload: OpeningDTO) -> OpeningVO:
    # 润色：开头候选
    system = (
        "你是技术文章开头改写助手。根据标题与正文，给出 3 种不同节奏的开头段落（可含 1～2 句），"
        "不要更换选题，不要复述整篇。"
        '只输出 JSON：{"candidates":[{"label":"string","text":"string"}]}'
    )
    user = (
        f"标题：{payload.title.strip() or '（无标题）'}\n\n"
        f"正文：\n{(payload.content_md or '')[:6000]}"
    )
    raw = ark_chat(user, system_prompt=system, temperature=0.4)
    return _parse_vo(raw, OpeningVO)
