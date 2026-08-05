# -*- coding: utf-8 -*-

import urllib.parse as urlparse
from collections.abc import Sequence

from bs4 import BeautifulSoup, Tag

from . import rule as rule_module
from .ebook import EPub
from .errors import NovelError
from .models import BookInfo, Chapter
from .rule import AnalyzeRule, NovelRule, biquge
from .utils import console, downloader, throttle
from .utils.downloader import Failure
from .utils.http import get_html, get_session


class NovelEngine:
    def __init__(self, novel_url: str, max_thread: int = 10) -> None:
        self._url = novel_url
        self._max_thread = max_thread or 10

        self.id: int = 0
        self.name: str | None = ""
        self.cover: str | None = ""  # 封面
        self.author: str | None = ""
        self.category: str | None = ""  # 分类

        # 两者都在 start() 里初始化，其余方法都在那之后才被调用
        self._epub: EPub | None = None
        self._site_rule: NovelRule | None = None

    @property
    def _rule(self) -> NovelRule:
        if self._site_rule is None:
            raise NovelError("站点规则未加载")
        return self._site_rule

    @property
    def _book(self) -> EPub:
        if self._epub is None:
            raise NovelError("电子书未初始化")
        return self._epub

    @property
    def charset(self) -> str:
        return self._rule.charset or "utf-8"

    @property
    def site_name(self) -> str:
        return self._rule.siteName or ""

    def _get_analyzer(self, content: str, element: BeautifulSoup | Tag) -> AnalyzeRule:
        return AnalyzeRule(self._rule, content, element)

    def _soup(self, content: str) -> BeautifulSoup:
        return BeautifulSoup(content, "html.parser")

    def _absolute(self, url: str | None) -> str | None:
        """规则里提取的地址可能是相对路径，统一补全成绝对地址。"""
        if not url:
            return url
        return urlparse.urljoin(self._url, url)

    def _apply_limits(self) -> None:
        """套用站点的限流配置"""
        interval = self._rule.requestInterval
        if interval:
            throttle.configure(float(interval))

        limit = self._rule.maxThread
        if limit and self._max_thread > int(limit):
            print("站点限制并发，线程数降为 %d" % int(limit))
            self._max_thread = int(limit)

    def prepare(self) -> list[Chapter]:
        """加载规则、解析书籍信息和目录，不下载正文。"""
        self._site_rule = rule_module.load(self._url)
        self._apply_limits()
        # 连接池要和并发数对齐，先于任何请求初始化
        get_session(pool_size=self._max_thread)

        # 解析基础信息
        basic_content = get_html(self._url, encoding=self.charset)
        if not basic_content:
            raise NovelError("无法访问 %s" % self._url)

        basic_analyzer = self._get_analyzer(basic_content, self._soup(basic_content))
        self._analyze_basic(basic_analyzer)

        if not self.name:
            raise NovelError("解析书名失败，站点规则可能已失效")

        return self._analyze_chapters(basic_analyzer)

    def start(self) -> None:
        chapters = self.prepare()

        # 书名解析成功才建目录，避免留下空壳
        self._epub = EPub(self.name or "", self._rule.siteName, self._rule.siteUrl)
        self._book.set_chapters(chapters)

        print("%s 作者:%s 共%d章" % (self.name, self.author, len(chapters)))
        failures = downloader.run(self._download_chapter, chapters, max_thread=self._max_thread)
        self._finish(failures)

    def _analyze_basic(self, analyzer: AnalyzeRule) -> None:
        if self._rule["isBiquge"]:
            self.name = analyzer.get_re_text(biquge.NAME)
            self.cover = analyzer.get_re_text(biquge.COVER)
            self.author = analyzer.get_re_text(biquge.AUTHOR)
            self.category = analyzer.get_re_text(biquge.CATEGORY)
        else:
            self.name = analyzer.get_text("ruleName")
            self.cover = analyzer.get_text("ruleCover")
            self.author = analyzer.get_text("ruleAuthor")
            self.category = analyzer.get_text("ruleCategory")

        self.cover = self._absolute(self.cover)

    def _analyze_chapters(self, basic_analyzer: AnalyzeRule) -> list[Chapter]:
        chapters_url = self._absolute(basic_analyzer.get_text("ruleChapterUrl"))

        # 目录可能独立成页，也可能就在详情页上
        if not chapters_url:
            chapters_analyzer = basic_analyzer
        else:
            content = get_html(chapters_url, encoding=self.charset)
            chapters_analyzer = self._get_analyzer(content, self._soup(content))

        chapters: list[Chapter] = []
        items = chapters_analyzer.get_elements("ruleChapterItems")
        for index, chapter_item in enumerate(items):
            analyzer = self._get_analyzer(str(chapter_item), chapter_item)
            content_url = analyzer.get_text("ruleContentUrl")
            chapters.append(
                {
                    "index": index,
                    "url": self._absolute(content_url) or "",
                    "name": analyzer.get_text("ruleChapterName"),
                }
            )

        if not chapters:
            raise NovelError("章节列表为空")

        return chapters

    def _download_chapter(self, chapter: Chapter) -> None:
        file_name = self._book.chapter_file_name(chapter["index"])
        if self._book.exists(file_name):
            return

        content_page = get_html(chapter["url"], encoding=self.charset)
        content = self._analyze_chapter(chapter, content_page)
        self._book.chapter(file_name, chapter["name"], content)

    def chapter_lines(self, content: str) -> list[str] | None:
        """从章节页取出正文各行，规则没命中时返回 None。"""
        analyzer = self._get_analyzer(content, self._soup(content))
        element = analyzer.get_element("ruleChapterContent")
        if not element:
            return None

        lines: list[str] = []
        ignore_lines = self._rule.ruleIgnoreLines
        for line in element.stripped_strings:
            strip_line = line.strip()
            if not strip_line or self._ignore_line(ignore_lines, strip_line):
                continue
            lines.append(strip_line)
        return lines

    def _analyze_chapter(self, chapter: Chapter, content: str) -> str:
        lines = self.chapter_lines(content)
        if lines is None:
            console.log("%s章节解析错误" % chapter["url"])
            return ""

        return "\n".join("<p>　　%s</p>" % line for line in lines)

    @staticmethod
    def _ignore_line(ignore_lines: Sequence[str] | None, line: str) -> bool:
        if not ignore_lines:
            return False
        return any(ignore_line in line for ignore_line in ignore_lines)

    def _finish(self, failures: list[Failure[Chapter]]) -> None:
        if failures:
            print("%d章下载失败：" % len(failures))
            for chapter, error in failures[:10]:
                print("  %s %s" % (chapter["name"], error))
            if len(failures) > 10:
                print("  ...")

        print("《%s》下载完成" % self.name)
        info: BookInfo = {
            "cover": self.cover,
            "book_id": self.id,
            "author": self.author,
            "book_subject": self.category,
            "book_url": self._url,
        }
        epub_file = self._book.make(info)
        print(epub_file)
