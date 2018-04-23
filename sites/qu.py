import urllib.parse as urlparse

from bs4 import BeautifulSoup

import utils.base as base
from sites.site import BaseNovel

__all__ = ["Qu"]


class Qu(BaseNovel):
    _source_site = "https://www.qu.la"
    _source_title = "笔趣阁"

    def parse_base_info(self, content):
        soup = BeautifulSoup(content, "html.parser")
        item = soup.select("#fmimg > img")[0]
        self._cover = urlparse.urljoin(self._novel_link, item["src"])

        self._name = soup.find("h1").string.strip()
        self._read_link = self._novel_link
        self._id = "qu:%s" % self._read_link[
                             self._read_link.rfind("/", 0, -1) + 1:-1]

        self._author = base.match(content, r'<meta property="og:novel:author" content="(.*)"/>') or ""
        self._subject = base.match(content, r'<meta property="og:novel:category" content="(.*)"/>') or ""

    def parse_chapter_list(self, content):
        """解析章节列表"""
        soup = BeautifulSoup(content, "html.parser")
        dt_items = soup.select("dt")
        # 忽略最新章节
        start_item = None
        for dt_item in dt_items:
            if "最新章节" in dt_item.string:
                continue
            start_item = dt_item
            break

        # 定位dd
        if start_item is None:
            chapter_items = soup.select("#list dd")
        else:
            chapter_items = start_item.find_next_siblings("dd") or []

        # 章节列表
        index = 0
        for chapter_item in chapter_items:
            self._chapter_list.append(
                dict(
                    index=index,
                    link=urlparse.urljoin(self._read_link, chapter_item.a["href"]),
                    title=chapter_item.a.string))
            index += 1

    def parse_chapter_content(self, chapter, content):
        """解析章节内容"""
        soup = BeautifulSoup(content, "html.parser")
        item = soup.find(id="content")
        lines = ["<p>　　%s</p>" % text for text in item.stripped_strings if text.strip() != "chaptererror();"]
        return "\n".join(lines)
