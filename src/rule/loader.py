# -*- coding: utf-8 -*-
"""站点规则的加载"""

import json
import urllib.parse as urlparse
from typing import Any

from ..errors import NovelError
from ..utils.paths import RULE_FILE


class NovelRule:
    """站点规则"""

    def __init__(self, site_rule: dict[str, Any]) -> None:
        self._site_rule = site_rule

    def __getattr__(self, name: str) -> Any:
        return self[name]

    def __getitem__(self, name: str) -> Any:
        value = self._site_rule.get(name)
        if isinstance(value, dict):
            return dict(value)

        if isinstance(value, list):
            return list(value)

        return value


def load(url: str) -> NovelRule:
    """按 URL 的域名找到对应的站点规则。"""
    try:
        with open(RULE_FILE, "rb") as file:
            json_rules = json.load(file)  # list
    except FileNotFoundError:
        raise NovelError("找不到规则文件 %s" % RULE_FILE)
    except json.JSONDecodeError as error:
        raise NovelError("规则文件格式错误：%s" % error)

    if not json_rules:
        raise NovelError("规则加载失败")

    hostname = urlparse.urlparse(url).hostname
    for site_rule in json_rules:
        site_url = site_rule.get("siteUrl") or ""
        if urlparse.urlparse(site_url).hostname == hostname:
            return NovelRule(site_rule)

    raise NovelError("找不到%s站点规则" % url)
