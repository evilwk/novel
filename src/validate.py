# -*- coding: utf-8 -*-
"""规则验证"""

from .engine import NovelEngine
from .errors import NovelError
from .models import Chapter
from .utils.http import get_html

# 正文预览的行数和每行截断长度
PREVIEW_LINES = 3
PREVIEW_WIDTH = 60


def _show(label: str, value: object) -> bool:
    """打印一条结果，返回是否命中。"""
    ok = bool(value)
    print("  %s %-6s %s" % ("✓" if ok else "✗", label, value if ok else "(未命中)"))
    return ok


def _ellipsis(line: str, width: int = PREVIEW_WIDTH) -> str:
    return line if len(line) <= width else line[:width] + "..."


def _check_basic(engine: NovelEngine) -> int:
    """书籍信息，书名缺失才算致命。"""
    print("书籍信息")
    _show("书名", engine.name)
    _show("作者", engine.author)
    _show("分类", engine.category)
    _show("封面", engine.cover)
    return 0 if engine.name else 1


def _check_chapters(chapters: list[Chapter]) -> int:
    print("\n目录 共%d章" % len(chapters))

    # 名称或链接缺失的章节，规则写错时通常是整批缺
    no_name = [c for c in chapters if not c["name"]]
    no_url = [c for c in chapters if not c["url"]]

    for chapter in chapters[:3]:
        print("  %-4d %s" % (chapter["index"], chapter["name"] or "(无名称)"))
        print("       %s" % (chapter["url"] or "(无链接)"))

    if len(chapters) > 3:
        print("  ... 末章 %s" % (chapters[-1]["name"] or "(无名称)"))

    problems = 0
    if no_name:
        print("  ✗ %d章缺名称，检查 ruleChapterName" % len(no_name))
        problems += 1

    if no_url:
        print("  ✗ %d章缺链接，检查 ruleContentUrl" % len(no_url))
        problems += 1

    return problems


def _check_content(engine: NovelEngine, chapter: Chapter) -> int:
    print("\n正文 %s" % chapter["name"])
    print("  %s" % chapter["url"])

    page = get_html(chapter["url"], encoding=engine.charset)
    if not page:
        print("  ✗ 页面抓取失败")
        return 1

    lines = engine.chapter_lines(page)
    if lines is None:
        print("  ✗ ruleChapterContent 未命中，正文元素没找到")
        return 1
    if not lines:
        print("  ✗ 命中了元素但内容为空，可能被 ruleIgnoreLines 全过滤了")
        return 1

    print("  ✓ %d行" % len(lines))
    for line in lines[:PREVIEW_LINES]:
        print("    %s" % _ellipsis(line))

    if len(lines) > PREVIEW_LINES:
        print("    ...")

    return 0


def run(url: str, chapter_index: int = 0) -> int:
    """验证 url 对应站点的规则，返回有问题的环节数。"""
    engine = NovelEngine(url)
    chapters = engine.prepare()

    print("站点 %s" % engine.site_name)
    print("编码 %s\n" % engine.charset)

    problems = _check_basic(engine)
    problems += _check_chapters(chapters)

    if chapter_index >= len(chapters):
        raise NovelError("只有%d章，取不到第%d章" % (len(chapters), chapter_index))

    problems += _check_content(engine, chapters[chapter_index])

    print("\n%s" % ("全部规则命中" if problems == 0 else "%d处有问题" % problems))
    return problems
