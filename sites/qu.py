import sites.biqu_parse as biqu
from .site import *

__all__ = ["Qu"]


class Qu(BaseNovel):
    source_site = "https://www.qu.la"
    source_title = "笔趣阁"

    def parse_base_info(self, content):
        biqu.info_from_meta(self, content)

    def parse_chapter_list(self, content):
        biqu.parse_chapters(self, "#list", content=content, multi_segment=True)

    @staticmethod
    def chapter_soup_select():
        return "#content"

    @staticmethod
    def chapter_line_filters():
        return ['chaptererror();', '<!--divstyle="color:#f00">']
