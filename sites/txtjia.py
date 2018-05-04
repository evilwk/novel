import urllib.parse as urlparse

from bs4 import BeautifulSoup

import sites.biqu_parse as biqu
import utils.base as base
from sites.site import BaseNovel

__all__ = ["TxtJia"]


class TxtJia(BaseNovel):
    _encode = "gbk"

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
        biqu.parse_chapters(self, BeautifulSoup(content, "html.parser"), False, ".list li")

    @staticmethod
    def chapter_soup_select():
        return "#booktext"
