import urllib.parse as urlparse

from bs4 import BeautifulSoup

import utils.base as base
from sites.site import BaseNovel

__all__ = ["Booktxt"]


class Booktxt(BaseNovel):
    _encode = "gbk"

    _source_site = "http://www.booktxt.net"
    _source_title = "顶点小说"

    def parse_base_info(self, content):
        soup = BeautifulSoup(content, "html.parser")
        item = soup.select("#fmimg > script")[0]
        img_script_url = urlparse.urljoin(self._novel_link, item["src"])
        img_script = base.get_html(img_script_url)
        self._cover = base.match(img_script, r"src=\'(.*?)\'")

        self._name = soup.find("h1").string.strip()
        self._read_link = self._novel_link
        self._id = "booktxt:%s" % self._read_link[
                                  self._read_link.rfind("/", 0, -1) + 1:-1]

        item = soup.find("div", id="info")
        item_html = item.prettify()
        self._author = base.match(item_html, "作    者：(.*)").strip()

        item = soup.select(".con_top a")[2]
        self._subject = item.string

    def parse_chapter_list(self, content):
        """解析章节列表"""
        soup = BeautifulSoup(content, "html.parser")
        dt_items = soup.select("dt")
        # 忽略最新章节
        start_item = None
        for dt_item in dt_items:
            if "最新章节" in dt_item.prettify():
                continue
            start_item = dt_item
            break

        # 定位dd
        if start_item is None:
            chapter_items = soup.select("#list dd")
        else:
            chapter_items = start_item.find_next_siblings("dd") or []

        # 章节列表
        index = 0
        for chapter_item in chapter_items:
            self._chapter_list.append(
                dict(
                    index=index,
                    link=urlparse.urljoin(self._read_link, chapter_item.a["href"]),
                    title=chapter_item.a.string))
            index += 1

    def parse_chapter_content(self, chapter, content):
        """解析章节内容"""
        soup = BeautifulSoup(content, "html.parser")
        item = soup.find(id="content")
        lines = []
        for line in item.stripped_strings:
            if line.strip() == 'chaptererror();':
                continue
            if '<!--divstyle="color:#f00">' in line:
                continue
            lines.append("<p>　　%s</p>" % line)
        return "\n".join(lines)
