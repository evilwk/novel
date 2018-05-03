from bs4 import BeautifulSoup

import sites.biqu_parse as biqu
from sites.site import BaseNovel

__all__ = ["Biqubook"]


class Biqubook(BaseNovel):
    _encode = "gbk"

    _source_site = "http://www.biqubook.com"
    _source_title = "笔趣阁"

    def parse_base_info(self, content):
        biqu.parse_info(self, BeautifulSoup(content, "html.parser"), content)

    def parse_chapter_list(self, content):
        biqu.parse_chapters(self, BeautifulSoup(content, "html.parser"), False, ".listmain dd")
