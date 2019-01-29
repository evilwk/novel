import sites.biqu_parse as biqu
from sites.site import BaseNovel

__all__ = ["Biqubook"]


class Biqubook(BaseNovel):
    _encode = "gbk"

    source_site = "http://www.biqubook.com"
    source_title = "笔趣阁"

    def parse_base_info(self, content):
        biqu.info_from_meta(self, content)

    def parse_chapter_list(self, content):
        biqu.parse_chapters(self, ".listmain", content=content, multi_segment=True)

    @staticmethod
    def chapter_soup_select():
        return "div.showtxt"
