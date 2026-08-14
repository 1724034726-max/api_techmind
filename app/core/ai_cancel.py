# 可取消标记：SSE 断开时停止上游方舟拉取
from __future__ import annotations

import threading


def new_cancel_event() -> threading.Event:
    """创建取消事件（set 后表示应停止）。"""
    return threading.Event()
