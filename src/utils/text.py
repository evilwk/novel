# -*- coding: utf-8 -*-

import re
from typing import overload


@overload
def match(text: str, pattern: str, /) -> str | None: ...


@overload
def match(text: str, pattern: str, second: str, /, *rest: str) -> list[str]: ...


def match(text: str, *patterns: str) -> str | list[str] | None:
    """匹配正则表达式的第一个捕获组。

    传入单个 pattern 时返回字符串或 None，传入多个时返回命中结果的列表。
    """
    if len(patterns) == 1:
        found = re.search(patterns[0], text, re.DOTALL)
        return found.group(1) if found else None

    matched: list[str] = []
    for pattern in patterns:
        found = re.search(pattern, text, re.DOTALL)
        if found:
            matched.append(found.group(1))

    return matched
