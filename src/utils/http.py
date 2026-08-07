# -*- coding: utf-8 -*-
"""HTTP 抓取"""

import threading
from os import PathLike
from typing import Any

import requests
import urllib3
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from . import console, throttle
from .config import get_network_proxy, get_network_timeout

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    " (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)

_session: requests.Session | None = None
_session_lock = threading.Lock()


def _build_session(pool_size: int) -> requests.Session:
    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT

    retry = Retry(
        total=5,
        backoff_factor=1.0,
        # 撞限流时所有线程会同时开始退避，加抖动免得它们再一起冲上去
        backoff_jitter=1.0,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET",),
        # 限流站点常在 429 里带 Retry-After，按它等更准
        respect_retry_after_header=True,
    )
    # 连接池要跟并发数对齐，否则线程会互相抢连接。
    adapter = HTTPAdapter(
        max_retries=retry,
        pool_connections=pool_size,
        pool_maxsize=pool_size,
    )
    session.mount("http://", adapter)
    session.mount("https://", adapter)

    proxy = get_network_proxy()
    # http:// 或 socks5h://，太短的值视为没有配置
    if len(proxy) >= 10:
        session.proxies = {"http": proxy, "https": proxy}

    return session


def get_session(pool_size: int = 10) -> requests.Session:
    global _session
    if _session is None:
        with _session_lock:
            if _session is None:
                _session = _build_session(pool_size)
    return _session


def get_response(url: str, **kwargs: Any) -> requests.Response | None:
    kwargs.setdefault("timeout", get_network_timeout())
    kwargs.setdefault("verify", False)
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    throttle.wait()
    try:
        return get_session().get(url, **kwargs)
    except Exception as error:
        console.log("request %s %s" % (url, error))
        return None


def get_html(url: str, encoding: str | None = None, **kwargs: Any) -> str:
    response = get_response(url, **kwargs)
    if not response:
        return ""

    if encoding:
        response.encoding = encoding

    return response.text


def download(url: str, file_name: str | PathLike[str], **kwargs: Any) -> bool:
    response = get_response(url, **kwargs)
    if not response:
        return False
    with open(file_name, "wb+") as file:
        file.write(response.content)

    return True
