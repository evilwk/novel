import urllib.parse as urlparse

import utils.base as base


def parse_info(novel, soup, content, script_img=False, author_from_meta=True):
    try:
        if script_img:
            item = soup.select("#fmimg > script")[0]
            img_script_url = urlparse.urljoin(novel._novel_link, item["src"])
            img_script = base.get_html(img_script_url)
            novel._cover = base.match(img_script, r"src=\'(.*?)\'")
        else:
            item = soup.select("#fmimg > img")[0]
            novel._cover = urlparse.urljoin(novel._novel_link, item["src"])
    except Exception as error:
        print(error)
        return

    novel._name = soup.find("h1").string.strip()
    novel._read_link = novel._novel_link
    novel._id = "%s:%s" % (base.get_url_domain(novel._source_site), novel._read_link[
                                                                    novel._read_link.rfind("/", 0, -1) + 1:-1])

    if author_from_meta:
        novel._author = base.match(content, r'<meta property="og:novel:author" content="(.*)"/>') or ""
        novel._subject = base.match(content, r'<meta property="og:novel:category" content="(.*)"/>') or ""


def parse_chapters(novel, soup, multi_dt, soup_select):
    if multi_dt:
        _parse_multi_dt(novel, soup, soup_select)
    else:
        chapter_items = soup.select(soup_select)

        # 章节列表
        index = 0
        for chapter_item in chapter_items:
            novel._chapter_list.append(
                dict(
                    index=index,
                    link=urlparse.urljoin(novel._read_link, chapter_item.a["href"]),
                    title=chapter_item.a.string))
            index += 1


def _parse_multi_dt(novel, soup, soup_select):
    chapter_root = soup.select(soup_select)[0]
    dt_items = chapter_root.select("dt")
    # 忽略最新章节
    start_item = None
    for dt_item in dt_items:
        if "最新章节" in dt_item.string:
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
        novel._chapter_list.append(
            dict(
                index=index,
                link=urlparse.urljoin(novel._read_link, chapter_item.a["href"]),
                title=chapter_item.a.string))
        index += 1
