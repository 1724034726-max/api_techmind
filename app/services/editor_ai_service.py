# 写作助手：方舟 LLM + SSE（提示词约束 Markdown 流式，结束后解析为 VO）
from __future__ import annotations

import re
import threading
from collections.abc import Callable, Iterator
from typing import TypeVar

from pydantic import BaseModel

from app.core.error_codes import ErrorCode
from app.core.exceptions import AppException, exception
from app.core.sse import format_sse
from app.integrations.ark import ark_chat, ark_chat_stream
from app.schemas.editor_ai import (
    ExpandDTO,
    ExpandVO,
    OpeningDTO,
    OpeningVO,
    SummaryDTO,
    SummaryVO,
    TextCandidateVO,
    TopicAnalyzeDTO,
    TopicAnalyzeVO,
    TopicAngleVO,
)

T = TypeVar("T", bound=BaseModel)

_EXPAND_SYSTEM = (
    "你是技术文章扩写助手。\n"
    "任务：根据标题与已有 Markdown，生成可「追加到文末」的初稿片段。\n"
    "硬性输出格式：\n"
    "1. 只输出 Markdown 正文（可用标题、列表、围栏代码块）。\n"
    "2. 禁止 JSON；禁止用 ```markdown 包裹整篇；禁止「好的」「如下」等前言后记。\n"
    "3. 不要重复已有正文，不要输出全文替换稿。\n"
    "正确示例开头：\n## 实现思路\n\n在生产环境中……\n"
    "错误示例（禁止）：\n"
    '{"appendix_md":"..."}\n'
)

_TOPIC_SYSTEM = (
    "你是 TechMind 技术社区的选题助手。\n"
    "根据关键词给出竞争洞察与 3 个差异化写作切口。\n"
    "硬性输出格式（只输出 Markdown，禁止 JSON）：\n\n"
    "## 洞察\n\n"
    "（一段竞争洞察）\n\n"
    "## 切口：{角度名}\n\n"
    "**标题**：工作标题\n"
    "**提示**：一句话竞争提示\n\n"
    "（此处起写 Markdown 大纲，直到下一个「## 切口」或文末）\n\n"
    "需要恰好 3 个「## 切口：」。不要前言后记。"
)

_SUMMARY_SYSTEM = (
    "你是技术文章导读助手。根据标题与正文，生成 3 条一句话导读，"
    "说明本文解决什么问题，语气专业克制，每条不超过 60 字。\n"
    "硬性输出格式（只输出 Markdown，禁止 JSON）：\n\n"
    "## 问题导向\n\n"
    "一句话导读\n\n"
    "## 结论先行\n\n"
    "一句话导读\n\n"
    "## 场景共鸣\n\n"
    "一句话导读\n\n"
    "二级标题即标签，正文即导读。不要更多章节，不要前言后记。"
)

_OPENING_SYSTEM = (
    "你是技术文章开头改写助手。根据标题与正文，给出 3 种不同节奏的开头（可含 1～2 句），"
    "不要更换选题，不要复述整篇。\n"
    "硬性输出格式（只输出 Markdown，禁止 JSON）：\n\n"
    "## 场景切入\n\n"
    "开头段落\n\n"
    "## 共鸣提问\n\n"
    "开头段落\n\n"
    "## 结论先行\n\n"
    "开头段落\n\n"
    "二级标题即标签，正文即开头。不要更多章节，不要前言后记。"
)


def _looks_like_json(text: str) -> bool:
    """粗判是否误输出了 JSON。"""
    head = (text or "").lstrip()[:40]
    return head.startswith("{") or head.startswith("[")


def _finalize_plain_md(raw: str) -> str:
    """校验非空且非 JSON 的 Markdown。"""
    text = (raw or "").strip()
    if not text:
        raise exception(ErrorCode.ERR_AI_BAD_RESPONSE)
    if _looks_like_json(text):
        raise exception(ErrorCode.ERR_AI_BAD_RESPONSE, detail="expected markdown not json")
    return text


def _parse_topic_md(raw: str) -> TopicAnalyzeVO:
    """按约定 Markdown 结构解析选题结果（仅拆「洞察/切口」二级标题）。"""
    text = _finalize_plain_md(raw)
    headers = list(re.finditer(r"(?m)^##\s+(洞察|切口\s*[:：].+)$", text))
    if not headers:
        raise exception(ErrorCode.ERR_AI_BAD_RESPONSE, detail="topic md missing sections")

    insight = ""
    angles: list[TopicAngleVO] = []

    for i, h in enumerate(headers):
        body_start = h.end()
        body_end = headers[i + 1].start() if i + 1 < len(headers) else len(text)
        body = text[body_start:body_end].strip()
        heading = h.group(1).strip()

        if heading.startswith("洞察"):
            insight = body
            continue

        angle = re.sub(r"^切口\s*[:：]\s*", "", heading).strip() or "切口"
        title = ""
        hint = ""
        tm = re.search(r"\*\*标题\*\*\s*[:：]\s*(.+)", body)
        hm = re.search(r"\*\*提示\*\*\s*[:：]\s*(.+)", body)
        if tm:
            title = tm.group(1).strip()
        if hm:
            hint = hm.group(1).strip()
        outline = body
        outline = re.sub(r"\*\*标题\*\*\s*[:：]\s*.+", "", outline, count=1)
        outline = re.sub(r"\*\*提示\*\*\s*[:：]\s*.+", "", outline, count=1)
        outline = outline.strip()
        angles.append(
            TopicAngleVO(
                angle=angle,
                title=title or angle,
                hint=hint,
                outline_md=outline,
            )
        )

    if not insight or not angles:
        raise exception(ErrorCode.ERR_AI_BAD_RESPONSE, detail="topic md parse failed")
    return TopicAnalyzeVO(insight=insight, angles=angles[:3])


def _parse_labeled_sections_md(raw: str) -> list[TextCandidateVO]:
    """解析「## label + 正文」候选列表。"""
    text = _finalize_plain_md(raw)
    parts = re.split(r"(?m)^##\s+", text)
    out: list[TextCandidateVO] = []
    for part in parts:
        block = part.strip()
        if not block:
            continue
        first, _, rest = block.partition("\n")
        label = first.strip()
        body = rest.strip()
        if not label or not body:
            continue
        out.append(TextCandidateVO(label=label, text=body))
    if len(out) < 1:
        raise exception(ErrorCode.ERR_AI_BAD_RESPONSE, detail="candidates md parse failed")
    return out[:3]


def _iter_md_sse(
    *,
    system: str,
    user: str,
    temperature: float,
    parse_done: Callable[[str], BaseModel],
    cancel: threading.Event | None = None,
) -> Iterator[str]:
    """Markdown 流式：逐 token delta，结束 parse_done → done；cancel 时尽快停止。"""
    chunks: list[str] = []
    try:
        yield format_sse("delta", {"text": ""})  # 立即冲刷响应头
        for delta in ark_chat_stream(
            user,
            system_prompt=system,
            temperature=temperature,
            cancel=cancel,
        ):
            if cancel is not None and cancel.is_set():
                return
            chunks.append(delta)
            yield format_sse("delta", {"text": delta})
        if cancel is not None and cancel.is_set():
            return
        vo = parse_done("".join(chunks))
        yield format_sse("done", vo.model_dump())
    except AppException as exc:
        if cancel is not None and cancel.is_set():
            return
        yield format_sse("error", {"code": exc.code, "message": exc.message})
    except Exception:
        if cancel is not None and cancel.is_set():
            return
        yield format_sse(
            "error",
            {
                "code": ErrorCode.ERR_AI_UPSTREAM.code,
                "message": ErrorCode.ERR_AI_UPSTREAM.message,
            },
        )


def analyze_topic(payload: TopicAnalyzeDTO) -> TopicAnalyzeVO:
    # 选题（同步）
    user = f"关键词：{payload.keyword.strip()}"
    raw = ark_chat(user, system_prompt=_TOPIC_SYSTEM, temperature=0.3)
    return _parse_topic_md(raw)


def iter_analyze_topic_sse(
    payload: TopicAnalyzeDTO,
    *,
    cancel: threading.Event | None = None,
) -> Iterator[str]:
    # 选题 SSE：MD 流式
    user = f"关键词：{payload.keyword.strip()}"
    yield from _iter_md_sse(
        system=_TOPIC_SYSTEM,
        user=user,
        temperature=0.3,
        parse_done=_parse_topic_md,
        cancel=cancel,
    )


def expand_draft(payload: ExpandDTO) -> ExpandVO:
    # 扩写（同步）
    user = (
        f"标题：{payload.title.strip() or '（无标题）'}\n\n"
        f"现有正文：\n{(payload.content_md or '').strip() or '（空，请写一篇可落地的初稿骨架）'}"
    )
    raw = ark_chat(user, system_prompt=_EXPAND_SYSTEM, temperature=0.4)
    return ExpandVO(appendix_md=_finalize_plain_md(raw))


def iter_expand_draft_sse(
    payload: ExpandDTO,
    *,
    cancel: threading.Event | None = None,
) -> Iterator[str]:
    # 扩写 SSE：MD 流式
    user = (
        f"标题：{payload.title.strip() or '（无标题）'}\n\n"
        f"现有正文：\n{(payload.content_md or '').strip() or '（空，请写一篇可落地的初稿骨架）'}"
    )
    yield from _iter_md_sse(
        system=_EXPAND_SYSTEM,
        user=user,
        temperature=0.4,
        parse_done=lambda raw: ExpandVO(appendix_md=_finalize_plain_md(raw)),
        cancel=cancel,
    )


def polish_summary(payload: SummaryDTO) -> SummaryVO:
    # 导读（同步一次性）
    user = (
        f"标题：{payload.title.strip() or '（无标题）'}\n\n"
        f"正文：\n{(payload.content_md or '')[:6000]}"
    )
    raw = ark_chat(user, system_prompt=_SUMMARY_SYSTEM, temperature=0.3)
    return SummaryVO(candidates=_parse_labeled_sections_md(raw))


def polish_opening(payload: OpeningDTO) -> OpeningVO:
    # 开头（同步一次性）
    user = (
        f"标题：{payload.title.strip() or '（无标题）'}\n\n"
        f"正文：\n{(payload.content_md or '')[:6000]}"
    )
    raw = ark_chat(user, system_prompt=_OPENING_SYSTEM, temperature=0.4)
    return OpeningVO(candidates=_parse_labeled_sections_md(raw))
