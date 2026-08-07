# -*- coding: utf-8 -*-
"""请求限速"""

import random
import threading
import time

# 默认抖动比例，间隔在 ±30% 内随机
DEFAULT_JITTER = 0.3

_lock = threading.Lock()
_interval = 0.0
_jitter = DEFAULT_JITTER
_next_time = 0.0


def configure(interval: float, jitter: float | None = None) -> None:
    """设置请求间隔，单位秒。0 表示不限速。

    jitter 是间隔的抖动比例，0.3 表示实际间隔在 ±30% 内随机取值。
    固定节奏的请求容易被站点当成机器识别，抖一下更像人在翻页。
    """
    global _interval, _jitter, _next_time
    with _lock:
        _interval = max(0.0, interval)
        _jitter = min(1.0, max(0.0, DEFAULT_JITTER if jitter is None else jitter))
        _next_time = 0.0


def _pick_interval() -> float:
    """本次要等的间隔，调用方需持有 _lock。"""
    if _jitter <= 0:
        return _interval
    return _interval * random.uniform(1.0 - _jitter, 1.0 + _jitter)


def wait() -> None:
    """必要时阻塞到下一个可发请求的时刻。"""
    global _next_time

    if _interval <= 0:
        return

    with _lock:
        now = time.monotonic()
        # 落后于计划就从当前时刻重新起算，避免空闲后突然连发
        start = max(now, _next_time)
        _next_time = start + _pick_interval()

    delay = start - now
    if delay > 0:
        time.sleep(delay)
