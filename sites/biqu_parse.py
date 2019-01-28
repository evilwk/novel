import urllib.parse as urlparse

import utils.base as base


def parse_info(novel, soup, content, script_img=False, author_from_meta=True):
    """解析小说基础信息，author和subject如果不能从meta从匹配，需要再额外处理"""
    try:
        if script_img:
            item = soup.select("#fmimg > script")[0]
            img_script_url = urlparse.urljoin(novel.novel_link, item["src"])
            img_script = base.get_html(img_script_url)
            novel.cover = base.match(img_script, r"src=\'(.*?)\'")
        else:
            item = soup.select(".info img")[0]
            novel.cover = urlparse.urljoin(novel.novel_link, item["src"])
    except Exception as error:
        print(error)
        return

    novel.name = soup.find("h2").string.strip()
    novel.read_link = novel.novel_link
    novel.id = novel.read_link[novel.read_link.rfind("/", 0, -1) + 1:-1]

    if author_from_meta:
        novel.author = base.match(content, r'<meta property="og:novel:author" content="(.*)"/>') or ""
        novel.subject = base.match(content, r'<meta property="og:novel:category" content="(.*)"/>') or ""


def parse_chapters(novel, soup, multi_segment, soup_select):
    """解析章节列表"""
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
