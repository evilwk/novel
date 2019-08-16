import sites.biqu_parse as biqu
from .site import *

__all__ = ["Biquyun"]


class Biquyun(BaseNovel):
    _encoding = "gbk"

    source_site = "http://www.biquyun.com"
    source_title = "笔趣阁"

    def parse_base_info(self, content):
        biqu.info_from_meta(self, content)

    def parse_chapter_list(self, content):
        biqu.parse_chapters(self, "#list dd", content=content)

    @staticmethod
    def chapter_soup_select():
        return "#content"
