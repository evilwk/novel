import urllib.parse as urlparse

from bs4 import BeautifulSoup

import sites.biqu_parse as biqu
import utils.base as base
from sites.site import BaseNovel

__all__ = ["Biquyun"]


class Biquyun(BaseNovel):
    _encode = "gbk"

    source_site = "http://www.biquyun.com"
    source_title = "笔趣阁"

    def parse_base_info(self, content):
        soup = BeautifulSoup(content, "html.parser")
        item = soup.select("#fmimg img")[0]
        self.cover = urlparse.urljoin(self.novel_link, item["src"])

        self.name = soup.find("h1").string.strip()
        self.read_link = self.novel_link
        self.id = self.read_link[self.read_link.rfind("/", 0, -1) + 1:-1]
        self.author = base.match(content, r'<meta property="og:novel:author" content="(.*)"/>') or ""
        self.subject = base.match(content, r'<meta property="og:novel:category" content="(.*)"/>') or ""

    def parse_chapter_list(self, content):
        biqu.parse_chapters(self, BeautifulSoup(content, "html.parser"), False, "#list dd")

    def chapter_soup_select():
        return "#content"
