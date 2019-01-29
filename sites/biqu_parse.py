import urllib.parse as urlparse

from bs4 import BeautifulSoup

import utils


def info_from_meta(novel, content):
    novel.id = novel.read_link[novel.read_link.rfind("/", 0, -1) + 1:-1]
    novel.read_link = novel.novel_link

    novel.name = utils.match(content, r'<meta\s+property="og:novel:book_name"\s+content="(.*)"\s*/>') or ""
    novel.cover = utils.match(content, r'<meta\s+property="og:image"\s+content="(.*)"\s*/>') or ""
    novel.author = utils.match(content, r'<meta\s+property="og:novel:author"\s+content="(.*)"\s*/>') or ""
    novel.subject = utils.match(content, r'<meta\s+property="og:novel:category"\s+content="(.*)"\s*/>') or ""


def parse_chapters(novel, soup_select, soup=None, content=None, multi_segment=False):
    """解析章节列表"""
    if not soup:
        soup = BeautifulSoup(content, "html.parser")
    if multi_segment:
        _parse_multi_segment(novel, soup, soup_select)
    else:
        chapter_items = soup.select(soup_select)

        # 章节列表
        index = 0
        for chapter_item in chapter_items:
            novel.chapter_list.append({
                'index': index,
                'link': urlparse.urljoin(novel.read_link, chapter_item.a["href"]),
                'title': chapter_item.a.string
            })
            index += 1


def _parse_multi_segment(novel, soup, soup_select):
    """解析多个dt分卷样式的章节列表"""
    chapter_root = soup.select(soup_select)[0]
    dt_items = chapter_root.select("dt")
    # 忽略最新章节
    start_item = None
    for dt_item in dt_items:
        if "最新章节" in dt_item.get_text():
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
        novel.chapter_list.append({
            'index': index,
            'link': urlparse.urljoin(novel.read_link, chapter_item.a["href"]),
            'title': chapter_item.a.string
        })
        index += 1
