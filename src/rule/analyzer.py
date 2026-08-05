# -*- coding: utf-8 -*-
"""按规则从页面里取内容。

规则有两种写法：
1. `re:` 前缀的走正则匹配整个页面源码，
2. CSS 选择器，用 `选择器@属性` 的形式取属性（`@text` 表示取文本）。
"""

from bs4 import BeautifulSoup, Tag

from ..utils import text
from .loader import NovelRule


class AnalyzeRule:
    def __init__(
        self,
        site_rule: NovelRule,
        content: str,
        element: BeautifulSoup | Tag,
    ) -> None:
        self._site_rule = site_rule
        self._content = content
        self._element = element

    @staticmethod
    def _is_re(rule: str) -> bool:
        return rule.startswith("re:")

    @staticmethod
    def _re_pattern(rule: str) -> str:
        """取出 `re:` 之后的正则本体。"""
        return rule[3:]

    @staticmethod
    def _selector_parts(rule: str) -> list[str]:
        """把 `选择器@属性` 拆成两段，没写属性时只有一段。"""
        return rule.split("@")

    @staticmethod
    def _get_attr(element: Tag, name: str) -> str:
        # 站点排版常留下大量缩进和换行，取到的值一律去掉首尾空白
        if name == "text":
            return element.get_text().strip()
        return str(element[name]).strip()

    def get_elements(self, rule_name: str) -> list[Tag]:
        rule = self._site_rule[rule_name]
        if not rule:
            return []
        parts = self._selector_parts(rule)
        if not parts:
            return []

        return list(self._element.select(parts[0]))

    def get_element(self, rule_name: str) -> Tag | None:
        elements = self.get_elements(rule_name)
        return elements[0] if elements else None

    def get_text(self, rule_name: str, default: str | None = None) -> str | None:
        rule = self._site_rule[rule_name]
        if not rule:
            return default

        if self._is_re(rule):
            return self.get_re_text(rule)

        texts = self.get_texts(rule_name)
        return texts[0] if texts else default

    def get_re_text(self, rule: str) -> str | None:
        matched = text.match(self._content, self._re_pattern(rule))
        return matched.strip() if matched else matched

    def get_texts(self, rule_name: str) -> list[str]:
        elements = self.get_elements(rule_name)
        if not elements:
            return []

        parts = self._selector_parts(self._site_rule[rule_name])
        if len(parts) <= 1:
            return []

        texts: list[str] = []
        for element in elements:
            try:
                texts.append(self._get_attr(element, parts[1]))
            except Exception:
                pass

        return texts
