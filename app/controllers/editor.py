# 写作助手 AI 路由（SSE 流式；断开可取消上游）
from __future__ import annotations

import asyncio
import threading
from collections.abc import AsyncIterator, Callable, Iterator
from typing import Any

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.core.ai_cancel import new_cancel_event
from app.core.rate_limit import check_ai_rate_limit
from app.deps import CurrentUser
from app.schemas.common import ApiResponse
from app.schemas.editor_ai import (
    ExpandDTO,
    OpeningDTO,
    OpeningVO,
    SummaryDTO,
    SummaryVO,
    TopicAnalyzeDTO,
)
from app.services import editor_ai_service

router = APIRouter(tags=["editor-ai"])

_SSE_HEADERS = {
    "Cache-Control": "no-cache, no-transform",
    "Connection": "keep-alive",
    "X-Accel-Buffering": "no",
}


async def _sse_from_sync(
    make_iter: Callable[[threading.Event], Iterator[str]],
) -> AsyncIterator[str]:
    """单线程消费同步生成器；客户端断开时 set cancel 并停止入队。"""
    loop = asyncio.get_running_loop()
    queue: asyncio.Queue[Any] = asyncio.Queue(maxsize=32)
    sentinel = object()
    cancel = new_cancel_event()

    async def enqueue(item: Any) -> bool:
        # 取消或队列满时尽快放弃，避免 worker 永久阻塞
        while not cancel.is_set():
            try:
                queue.put_nowait(item)
                return True
            except asyncio.QueueFull:
                await asyncio.sleep(0.05)
        return False

    def worker() -> None:
        try:
            for chunk in make_iter(cancel):
                if cancel.is_set():
                    break
                ok = asyncio.run_coroutine_threadsafe(enqueue(chunk), loop).result(
                    timeout=180
                )
                if not ok:
                    break
        except Exception as exc:  # noqa: BLE001 — 传入异步侧
            if not cancel.is_set():
                try:
                    asyncio.run_coroutine_threadsafe(enqueue(exc), loop).result(
                        timeout=5
                    )
                except Exception:
                    pass
        finally:
            try:
                asyncio.run_coroutine_threadsafe(enqueue(sentinel), loop).result(
                    timeout=5
                )
            except Exception:
                pass

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()

    try:
        while True:
            item = await queue.get()
            if item is sentinel:
                break
            if isinstance(item, Exception):
                # 已开流后尽量走 SSE error 帧（由 service 产出）；裸异常则结束
                break
            yield str(item)
            await asyncio.sleep(0)
    finally:
        cancel.set()
        # 排空残留，避免 worker 卡在满队列
        while True:
            try:
                queue.get_nowait()
            except asyncio.QueueEmpty:
                break


def _sse(make_iter: Callable[[threading.Event], Iterator[str]]) -> StreamingResponse:
    """包装为 text/event-stream 响应。"""
    return StreamingResponse(
        _sse_from_sync(make_iter),
        media_type="text/event-stream",
        headers=_SSE_HEADERS,
    )


@router.post("/ai/topic-analyze")
def topic_analyze(
    payload: TopicAnalyzeDTO,
    current_user: CurrentUser,
) -> StreamingResponse:
    # 选题分析 SSE（需登录）
    check_ai_rate_limit(current_user.id)
    return _sse(
        lambda cancel: editor_ai_service.iter_analyze_topic_sse(payload, cancel=cancel)
    )


@router.post("/ai/expand")
def expand(
    payload: ExpandDTO,
    current_user: CurrentUser,
) -> StreamingResponse:
    # 大纲扩写 SSE
    check_ai_rate_limit(current_user.id)
    return _sse(
        lambda cancel: editor_ai_service.iter_expand_draft_sse(payload, cancel=cancel)
    )


@router.post("/ai/summary", response_model=ApiResponse[SummaryVO])
def summary(
    payload: SummaryDTO,
    current_user: CurrentUser,
) -> ApiResponse[SummaryVO]:
    # 导读候选：一次性 JSON（非 SSE）
    check_ai_rate_limit(current_user.id)
    data = editor_ai_service.polish_summary(payload)
    return ApiResponse.ok(data)


@router.post("/ai/opening", response_model=ApiResponse[OpeningVO])
def opening(
    payload: OpeningDTO,
    current_user: CurrentUser,
) -> ApiResponse[OpeningVO]:
    # 开头候选：一次性 JSON（非 SSE）
    check_ai_rate_limit(current_user.id)
    data = editor_ai_service.polish_opening(payload)
    return ApiResponse.ok(data)
