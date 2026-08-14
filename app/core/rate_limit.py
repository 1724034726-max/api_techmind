# 简单内存限流（单进程；多 worker 各自计数）
from __future__ import annotations

import threading
import time

from app.core.error_codes import ErrorCode
from app.core.exceptions import exception

_lock = threading.Lock()
# user_id -> 近期请求时间戳（monotonic）
_hits: dict[int, list[float]] = {}


def check_ai_rate_limit(
    user_id: int,
    *,
    limit: int = 8,
    window_sec: float = 60.0,
) -> None:
    """写作 AI：每用户滑动窗口限流；超限抛 ERR_AI_RATE_LIMITED。"""
    now = time.monotonic()
    with _lock:
        recent = [t for t in _hits.get(user_id, []) if now - t < window_sec]
        if len(recent) >= limit:
            raise exception(ErrorCode.ERR_AI_RATE_LIMITED, http_status=429)
        recent.append(now)
        _hits[user_id] = recent
        # 防止字典无限增长：偶发清理过期用户
        if len(_hits) > 4096:
            stale = [uid for uid, ts in _hits.items() if not ts or now - ts[-1] >= window_sec]
            for uid in stale[:512]:
                _hits.pop(uid, None)
