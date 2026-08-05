# -*- coding: utf-8 -*-
"""请求限速"""

import threading
import time

_lock = threading.Lock()
_interval = 0.0
_next_time = 0.0


def configure(interval: float) -> None:
    """设置请求间隔，单位秒。0 表示不限速。"""
    global _interval, _next_time
    with _lock:
        _interval = max(0.0, interval)
        _next_time = 0.0


def wait() -> None:
    """必要时阻塞到下一个可发请求的时刻。"""
    global _next_time

    if _interval <= 0:
        return

    with _lock:
        now = time.monotonic()
        # 落后于计划就从当前时刻重新起算，避免空闲后突然连发
        start = max(now, _next_time)
        _next_time = start + _interval

    delay = start - now
    if delay > 0:
        time.sleep(delay)
