import sites.biqu_parse as biqu
from sites.site import BaseNovel

__all__ = ["Booktxt"]


class Booktxt(BaseNovel):
    _encode = "gbk"

    source_site = "http://www.booktxt.net"
    source_title = "顶点小说"

    def parse_base_info(self, content):
        biqu.info_from_meta(self, content)

    def parse_chapter_list(self, content):
        biqu.parse_chapters(self, "#list", content=content, multi_segment=True)

    @staticmethod
    def chapter_soup_select():
        return "#content"

