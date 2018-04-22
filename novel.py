# coding:utf-8
import concurrent.futures
import abc
import shutil
import subprocess
from bs4 import BeautifulSoup
import base
import urllib.parse as urlparse
import os
import string
import sys
import threading


class BaseNovel:
    __metaclass__ = abc.ABCMeta

    encode = "utf-8"

    id = ""
    name = ""
    cover = ""  # 封面
    author = ""
    subject = ""  # 分类

    source_title = ""  # 网站标题
    source_site = ""  # 网站地址

    read_page_link = ""  # 阅读页链接
    chapter_list = []  # 章节列表 {link: "", title: ""}

    def __init__(self, novel_link, max_thread=10):
        self.novel_link = novel_link

        self.lock = threading.Lock()
        self.futures = []
        self.pool = concurrent.futures.ThreadPoolExecutor(
            max_workers=max_thread)

    def __call__(self):
        # 解析基础信息
        intro_page = base.get_html(self.novel_link, encode=self.encode)
        self.parse_base_info(intro_page)
        # 创建目录
        novel_dir = os.path.join("./novel", self.name)
        if not os.path.exists(novel_dir):
            os.makedirs(os.path.join(novel_dir, "META-INF"))

        # 解析章节列表
        if self.read_page_link is None or self.read_page_link == '':
            return

        read_page = base.get_html(self.read_page_link, encode=self.encode)
        self.parse_chapter_list(read_page)
        print("%s 作者:%s 共%d章" % (self.name, self.author,
                                 len(self.chapter_list)))
        for chapter in self.chapter_list:
            self.futures.append(
                self.pool.submit(self._download_chapter_content, chapter))
        # 等待结束
        concurrent.futures.wait(self.futures)
        print(" " * 30, end='\r')
        self._make_epub()
        self._make_mobi()

    def _make_epub(self):
        print("开始生成epub电子书...")
        # content.opf
        manifest = []
        spine = []
        # toc
        nav = []

        index = 1
        nav_index = 2
        for chapter in self.chapter_list:
            file_id = "chapter_%d" % chapter["index"]
            file_name = "chapter_%d.html" % chapter["index"]
            manifest.append(
                '<item id="{0}" href="{0}.html" media-type="application/xhtml+xml"/>'.
                    format(file_id))
            spine.append('<itemref idref="{0}"/>'.format(file_id))

            nav.append(
                '<navPoint id="{0}" playOrder="{1}"><navLabel><text>{2}</text></navLabel><content src="{0}.html"/></navPoint>'.
                    format(file_id, nav_index, chapter["title"]))
            index += 1
            nav_index += 1

        self._make_temple(
            "content.opf",
            "content.opf",
            title=self.name,
            bookid=self.id,
            author=self.author,
            create_time=self._get_time(),
            source_title=self.source_title,
            source_site=self.source_site,
            book_subject=self.subject,
            manifest_item="\n".join(manifest),
            spine_item="\n".join(spine))
        self._make_temple(
            "toc.ncx", "toc.ncx", bookid=self.id, nav_point='\n'.join(nav))
        self._make_temple(
            "title.xhtml",
            "title.xhtml",
            book_link=self.novel_link,
            book_title=self.name,
            source_title=self.source_title,
            source_site=self.source_site,
            book_subject=self.subject)

        self._copy_file('mimetype', 'stylesheet.css',
                        "META-INF/container.xml")
        base.download(self.cover, "./novel/%s/cover.jpg" % self.name)
        base.make_zip(
            os.path.join("./novel", self.name), "./novel/%s.epub" % self.name)

    def _make_mobi(self):
        file_name = "./novel/%s.epub" % self.name
        if not os.path.exists(file_name):
            return
        if not os.path.exists("kindlegen.exe"):
            return

        print("开始生成Mobi电子书...")
        try:
            pipe = subprocess.Popen(
                [os.path.abspath("kindlegen.exe"), file_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)
            pipe.communicate()
        except Exception as error:
            print(error)

    def _copy_file(self, *file_names):
        for name in file_names:
            shutil.copy("./epub_temple/%s" % name,
                        "./novel/%s/%s" % (self.name, name))

    def _get_time(self):
        import time
        return time.asctime(time.localtime(time.time()))

    def _make_temple(self, in_file_name, out_file_name, **temple_args):
        with open(
                "./epub_temple/%s" % in_file_name,
                encoding="utf-8") as in_file:
            temple = in_file.read()
            out_file_content = string.Template(temple).substitute(temple_args)
            with open(
                    "./novel/%s/%s" % (self.name, out_file_name),
                    "w+",
                    encoding="utf-8") as out_file:
                out_file.write(out_file_content)

    def _download_chapter_content(self, chapter):
        content_page = base.get_html(chapter["link"], encode=self.encode)
        novel_chapter = self.parse_chapter_content(chapter, content_page)
        self._make_temple(
            "content.html",
            "chapter_%d.html" % chapter["index"],
            chapter_title=chapter["title"],
            chapter_content=novel_chapter)
        self._show_percent()

    def _show_percent(self):
        with (self.lock):
            count = len(self.futures)
            complete = len(
                [future for future in self.futures if future.done()])
            percent = complete * 1.0 / count * 100
            sys.stdout.write('下载进度：%d/%d %.2f%%\r' % (complete, count,
                                                      percent))
            sys.stdout.flush()

    @abc.abstractmethod
    def parse_base_info(self, content):
        """解析基础信息"""
        pass

    @abc.abstractmethod
    def parse_chapter_list(self, content):
        """解析章节列表"""
        pass

    @classmethod
    def parse_chapter_content(self, chapter, content_page):
        """解析章节内容"""
        pass


class TxtJia(BaseNovel):
    encode = "gbk"

    source_site = "https://www.txtjia.com"
    source_title = "TXT之家"

    def parse_base_info(self, content):
        soup = BeautifulSoup(content, "html.parser")
        self.cover = soup.find("img", id="BookImage")["src"]

        self.name = soup.find("h2").string.strip()
        item = soup.find("a", class_="readnow")
        self.read_page_link = urlparse.urljoin(self.novel_link, item["href"])
        self.id = "txtjia:%s" % self.read_page_link[
                                self.read_page_link.rfind("/", 0, -1) + 1:-1]

        item = soup.find("p", class_="intr")
        item_html = item.prettify()
        self.author = base.match(item_html, "作者：(.*)").strip()
        self.subject = item.find("a").string
        item = soup.find("p", class_="con")

    def parse_chapter_list(self, content):
        """解析章节列表"""
        soup = BeautifulSoup(content, "html.parser")
        chapter_items = soup.select(".list li a")
        index = 0
        for chapter_item in chapter_items:
            self.chapter_list.append(
                dict(
                    index=index,
                    link=urlparse.urljoin(self.read_page_link, chapter_item[
                        "href"]),
                    title=chapter_item.string))
            index += 1
        return self.chapter_list

    def parse_chapter_content(self, chapter, content):
        """解析章节内容"""
        soup = BeautifulSoup(content, "html.parser")
        item = soup.find(id="booktext")
        lines = ["<p>　　%s</p>" % text for text in item.stripped_strings]
        return "\n".join(lines)


def main(*urls):
    executors = {"txtjia": TxtJia}
    for url in urls:
        domain = base.get_url_domain(url)
        if domain in executors.keys():
            novel = executors[domain](url)
            novel()


if __name__ == '__main__':
    main(*sys.argv[1:])
