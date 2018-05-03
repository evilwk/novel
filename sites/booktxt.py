from bs4 import BeautifulSoup

import sites.biqu_parse as biqu
import utils.base as base
from sites.site import BaseNovel

__all__ = ["Booktxt"]


class Booktxt(BaseNovel):
    _encode = "gbk"

    _source_site = "http://www.booktxt.net"
    _source_title = "顶点小说"

    def parse_base_info(self, content):
        soup = BeautifulSoup(content, "html.parser")
        biqu.parse_info(self, soup, content, script_img=True, author_from_meta=False)

        item = soup.find("div", id="info")
        item_html = item.prettify()
        self._author = base.match(item_html, "作    者：(.*)").strip()

        item = soup.select(".con_top a")[2]
        self._subject = item.string

    def parse_chapter_list(self, content):
        biqu.parse_chapters(self, BeautifulSoup(content, "html.parser"), True, "#list")
