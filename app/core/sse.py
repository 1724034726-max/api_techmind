# SSE 帧格式化
from __future__ import annotations

import json
from typing import Any


def format_sse(event: str, data: Any) -> str:
    """编码一条 SSE：event + JSON data。"""
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":"))
    return f"event: {event}\ndata: {payload}\n\n"
