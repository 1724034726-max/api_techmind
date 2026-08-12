# 雪花 ID 生成器（64 位，应用层写入主键）
from __future__ import annotations

import threading
import time

from app.config import get_settings

# Twitter 雪花：时间戳 | 数据中心 | 机器 | 序列
_EPOCH_MS = 1_609_459_200_000  # 2021-01-01 UTC
_WORKER_BITS = 5
_DATACENTER_BITS = 5
_SEQUENCE_BITS = 12
_MAX_WORKER_ID = (1 << _WORKER_BITS) - 1
_MAX_DATACENTER_ID = (1 << _DATACENTER_BITS) - 1
_SEQUENCE_MASK = (1 << _SEQUENCE_BITS) - 1
_WORKER_SHIFT = _SEQUENCE_BITS
_DATACENTER_SHIFT = _SEQUENCE_BITS + _WORKER_BITS
_TIMESTAMP_SHIFT = _SEQUENCE_BITS + _WORKER_BITS + _DATACENTER_BITS


class SnowflakeGenerator:
    """线程安全的雪花 ID 生成器。"""

    def __init__(self, worker_id: int, datacenter_id: int) -> None:
        if not 0 <= worker_id <= _MAX_WORKER_ID:
            raise ValueError(f"worker_id 超出范围 0..{_MAX_WORKER_ID}")
        if not 0 <= datacenter_id <= _MAX_DATACENTER_ID:
            raise ValueError(f"datacenter_id 超出范围 0..{_MAX_DATACENTER_ID}")
        self.worker_id = worker_id
        self.datacenter_id = datacenter_id
        self._lock = threading.Lock()
        self._sequence = 0
        self._last_timestamp = -1

    def next_id(self) -> int:
        # 生成下一个雪花 ID
        with self._lock:
            timestamp = self._current_millis()
            if timestamp < self._last_timestamp:
                # 时钟回拨时等待追上
                timestamp = self._wait_until(self._last_timestamp)
            if timestamp == self._last_timestamp:
                self._sequence = (self._sequence + 1) & _SEQUENCE_MASK
                if self._sequence == 0:
                    timestamp = self._wait_until(self._last_timestamp)
            else:
                self._sequence = 0
            self._last_timestamp = timestamp
            return (
                ((timestamp - _EPOCH_MS) << _TIMESTAMP_SHIFT)
                | (self.datacenter_id << _DATACENTER_SHIFT)
                | (self.worker_id << _WORKER_SHIFT)
                | self._sequence
            )

    @staticmethod
    def _current_millis() -> int:
        return int(time.time() * 1000)

    def _wait_until(self, last_timestamp: int) -> int:
        timestamp = self._current_millis()
        while timestamp <= last_timestamp:
            timestamp = self._current_millis()
        return timestamp


_generator: SnowflakeGenerator | None = None
_generator_lock = threading.Lock()


def get_snowflake() -> SnowflakeGenerator:
    # 懒加载单例，读取配置中的 worker / datacenter
    global _generator
    if _generator is None:
        with _generator_lock:
            if _generator is None:
                settings = get_settings()
                _generator = SnowflakeGenerator(
                    worker_id=settings.snowflake_worker_id,
                    datacenter_id=settings.snowflake_datacenter_id,
                )
    return _generator


def next_id() -> int:
    """生成下一个雪花主键。"""
    return get_snowflake().next_id()
