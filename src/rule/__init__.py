# -*- coding: utf-8 -*-
"""站点规则：加载 novel.json 并按规则解析页面。"""

from . import biquge
from .analyzer import AnalyzeRule
from .loader import NovelRule, load

__all__ = ["AnalyzeRule", "NovelRule", "biquge", "load"]
