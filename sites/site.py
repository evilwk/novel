import abc
import os
import shutil
import string
import subprocess
import time

import utils.base as base
from utils.download import Downloader

nav_point_temple = """        <navPoint id="{0}" playOrder="{1}">
            <navLabel>
                <text>{2}</text>
            </navLabel>
            <content src="{0}.html"/>
        </navPoint>"""

manifest_item_temple = '    <item id="{0}" href="{0}.html" media-type="application/xhtml+xml"/>'

spine_item_temple = '    <itemref idref="{0}"/>'


class BaseNovel:
    __metaclass__ = abc.ABCMeta

    _encode = "utf-8"

    _id = ""
    _name = ""
    _cover = ""  # 封面
    _author = ""
    _subject = ""  # 分类

    _source_title = ""  # 网站标题
    _source_site = ""  # 网站地址

    _read_link = ""  # 阅读页链接
    _chapter_list = []  # 章节列表 {link: "", title: ""}

    def __init__(self, novel_link, max_thread=10):
        self._novel_link = novel_link
        self._downloader = Downloader(max_thread=max_thread, finish_func=self._download_finish)

    def __call__(self):
        # 解析基础信息
        intro_page = base.get_html(self._novel_link, encode=self._encode)
        self.parse_base_info(intro_page)
        # 创建目录
        self._novel_dir = os.path.join("./novel", self._name)
        if not os.path.exists(self._novel_dir):
            os.makedirs(os.path.join(self._novel_dir, "META-INF"))

        # 解析章节列表
        if self._read_link is None or self._read_link == '':
            print("没有小说目录页面")
            return

        if self._read_link == self._novel_link:
            self.parse_chapter_list(intro_page)
        else:
            read_page = base.get_html(self._read_link, encode=self._encode)
            self.parse_chapter_list(read_page)

        if not self._chapter_list:
            print("章节列表为空")
            return
        print("%s 作者:%s 共%d章" % (self._name, self._author,
                                 len(self._chapter_list)))
        for chapter in self._chapter_list:
            self._downloader.submit(self._download_chapter_content, chapter)

        self._downloader.start()

    def _download_finish(self):
        print("")
        print("《%s》下载完成" % self._name)
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
        for chapter in self._chapter_list:
            file_id = "chapter_%d" % chapter["index"]
            manifest.append(manifest_item_temple.format(file_id))
            spine.append(spine_item_temple.format(file_id))
            nav.append(nav_point_temple.format(file_id, nav_index, chapter["title"]))
            index += 1
            nav_index += 1

        self._make_temple("content.opf",
                          title=self._name,
                          bookid=self._id,
                          author=self._author,
                          create_time=self._get_time(),
                          source_title=self._source_title,
                          source_site=self._source_site,
                          book_subject=self._subject,
                          manifest_item="\n".join(manifest),
                          spine_item="\n".join(spine))
        self._make_temple("toc.ncx",
                          bookid=self._id, nav_point='\n'.join(nav))
        self._make_temple("title.xhtml",
                          book_link=self._novel_link,
                          book_title=self._name,
                          source_title=self._source_title,
                          source_site=self._source_site,
                          book_subject=self._subject)

        self._copy_file('mimetype', 'stylesheet.css', "META-INF/container.xml")
        base.download(self._cover, os.path.join(self._novel_dir, "cover.jpg"))

        epub_file_name = "./novel/%s.epub" % self._name
        base.make_zip(self._novel_dir, epub_file_name)
        print(os.path.abspath(epub_file_name))

    @staticmethod
    def _get_time():
        return time.asctime(time.localtime(time.time()))

    def _make_mobi(self):
        epub_file_name = "./novel/%s.epub" % self._name
        mobi_file_name = "./novel/%s.mobi" % self._name
        tool_file = './tool/kindlegen.exe'
        if not os.path.exists(epub_file_name):
            return
        if not os.path.exists(tool_file):
            return

        print("开始生成Mobi电子书...")
        try:
            pipe = subprocess.Popen(
                [os.path.abspath(tool_file), epub_file_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)
            pipe.communicate()
            print(os.path.abspath(mobi_file_name))
        except Exception as error:
            print(error)

    def _copy_file(self, *file_names):
        for name in file_names:
            shutil.copy("./epub_temple/%s" % name,
                        os.path.join(self._novel_dir, name))

    def _make_temple(self, in_file_name, out_file_name=None, **temple_args):
        if not out_file_name:
            out_file_name = in_file_name
        with open("./epub_temple/%s" % in_file_name, encoding="utf-8") as in_file:
            temple = in_file.read()
            out_file_content = string.Template(temple).substitute(temple_args)
            with open(os.path.join(self._novel_dir, out_file_name), "w+", encoding="utf-8") as out_file:
                out_file.write(out_file_content)

    def _download_chapter_content(self, chapter):
        chapter_file_name = "chapter_%d.html" % chapter["index"]
        out_file_name = os.path.join(self._novel_dir, chapter_file_name)
        if not os.path.exists(out_file_name):
            content_page = base.get_html(chapter["link"], encode=self._encode)
            novel_chapter = self.parse_chapter_content(chapter, content_page)
            self._make_temple(
                "content.html",
                "chapter_%d.html" % chapter["index"],
                chapter_title=chapter["title"],
                chapter_content=novel_chapter)

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
