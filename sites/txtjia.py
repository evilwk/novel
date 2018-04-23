import urllib.parse as urlparse

from bs4 import BeautifulSoup

import utils.base as base
from sites.site import BaseNovel

__all__ = ["TxtJia"]


class TxtJia(BaseNovel):
    _encode = "gbk"

    _source_site = "https://www.txtjia.com"
    _source_title = "TXT之家"

    def parse_base_info(self, content):
        soup = BeautifulSoup(content, "html.parser")
        self._cover = soup.find("img", id="BookImage")["src"]

        self._name = soup.find("h2").string.strip()
        item = soup.find("a", class_="readnow")
        self._read_link = urlparse.urljoin(self._novel_link, item["href"])
        self._id = "txtjia:%s" % self._read_link[
                                 self._read_link.rfind("/", 0, -1) + 1:-1]

        item = soup.find("p", class_="intr")
        item_html = item.prettify()
        self._author = base.match(item_html, "作者：(.*)").strip()
        self._subject = item.find("a").string

    def parse_chapter_list(self, content):
        """解析章节列表"""
        soup = BeautifulSoup(content, "html.parser")
        chapter_items = soup.select(".list li a")
        index = 0
        for chapter_item in chapter_items:
            self._chapter_list.append(
                dict(
                    index=index,
                    link=urlparse.urljoin(self._read_link, chapter_item["href"]),
                    title=chapter_item.string))
            index += 1

    def parse_chapter_content(self, chapter, content):
        """解析章节内容"""
        soup = BeautifulSoup(content, "html.parser")
        item = soup.find(id="booktext")
        lines = ["<p>　　%s</p>" % text for text in item.stripped_strings]
        return "\n".join(lines)
