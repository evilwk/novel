import urllib.parse as urlparse

from bs4 import BeautifulSoup

import utils.base as base
from sites.site import BaseNovel

__all__ = ["Biquge"]


class Biquge(BaseNovel):
    _encode = "gbk"

    _source_site = "https://www.biquge.com.tw"
    _source_title = "笔趣阁"

    def parse_base_info(self, content):
        soup = BeautifulSoup(content, "html.parser")
        item = soup.select("#fmimg > img")[0]
        self._cover = urlparse.urljoin(self._novel_link, item["src"])

        self._name = soup.find("h1").string.strip()
        self._read_link = self._novel_link
        self._id = "biquge:%s" % self._read_link[
                                 self._read_link.rfind("/", 0, -1) + 1:-1]

        self._author = base.match(content, r'<meta property="og:novel:author" content="(.*)"/>') or ""
        self._subject = base.match(content, r'<meta property="og:novel:category" content="(.*)"/>') or ""

    def parse_chapter_list(self, content):
        """解析章节列表"""
        soup = BeautifulSoup(content, "html.parser")
        chapter_items = soup.select("#list dd")

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
        lines = ["<p>　　%s</p>" % text for text in item.stripped_strings]
        return "\n".join(lines)
