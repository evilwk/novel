from sites.site import BaseNovel
from bs4 import BeautifulSoup
import sys

sys.path.append("..")
import base
import urllib.parse as urlparse

__all__ = ["TxtJia"]


class TxtJia(BaseNovel):
    encode = "gbk"

    source_site = "https://www.txtjia.com"
    source_title = "TXT之家"

    def parse_base_info(self, content):
        soup = BeautifulSoup(content, "html.parser")
        self.cover = soup.find("img", id="BookImage")["src"]

        self.name = soup.find("h2").string.strip()
        item = soup.find("a", class_="readnow")
        self.read_link = urlparse.urljoin(self.novel_link, item["href"])
        self.id = "txtjia:%s" % self.read_link[
                                self.read_link.rfind("/", 0, -1) + 1:-1]

        item = soup.find("p", class_="intr")
        item_html = item.prettify()
        self.author = base.match(item_html, "作者：(.*)").strip()
        self.subject = item.find("a").string

    def parse_chapter_list(self, content):
        """解析章节列表"""
        soup = BeautifulSoup(content, "html.parser")
        chapter_items = soup.select(".list li a")
        index = 0
        for chapter_item in chapter_items:
            self.chapter_list.append(
                dict(
                    index=index,
                    link=urlparse.urljoin(self.read_link, chapter_item["href"]),
                    title=chapter_item.string))
            index += 1

    def parse_chapter_content(self, chapter, content):
        """解析章节内容"""
        soup = BeautifulSoup(content, "html.parser")
        item = soup.find(id="booktext")
        lines = ["<p>　　%s</p>" % text for text in item.stripped_strings]
        return "\n".join(lines)
