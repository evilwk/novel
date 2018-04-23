import abc
import concurrent.futures
import os
import shutil
import string
import subprocess
import threading

import utils.base as base

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

    encode = "utf-8"

    id = ""
    name = ""
    cover = ""  # 封面
    author = ""
    subject = ""  # 分类

    source_title = ""  # 网站标题
    source_site = ""  # 网站地址

    read_link = ""  # 阅读页链接
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
        self.novel_dir = os.path.join("./novel", self.name)
        if not os.path.exists(self.novel_dir):
            os.makedirs(os.path.join(self.novel_dir, "META-INF"))
        print(os.path.abspath(self.novel_dir))

        # 解析章节列表
        if self.read_link is None or self.read_link == '':
            print("没有小说目录页面")
            return

        if self.read_link == self.novel_link:
            self.parse_chapter_list(intro_page)
        else:
            read_page = base.get_html(self.read_link, encode=self.encode)
            self.parse_chapter_list(read_page)

        if not self.chapter_list:
            print("章节列表为空")
            return
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
            manifest.append(manifest_item_temple.format(file_id))
            spine.append(spine_item_temple.format(file_id))
            nav.append(nav_point_temple.format(file_id, nav_index, chapter["title"]))
            index += 1
            nav_index += 1

        self._make_temple("content.opf",
                          title=self.name,
                          bookid=self.id,
                          author=self.author,
                          create_time=self._get_time(),
                          source_title=self.source_title,
                          source_site=self.source_site,
                          book_subject=self.subject,
                          manifest_item="\n".join(manifest),
                          spine_item="\n".join(spine))
        self._make_temple("toc.ncx",
                          bookid=self.id, nav_point='\n'.join(nav))
        self._make_temple("title.xhtml",
                          book_link=self.novel_link,
                          book_title=self.name,
                          source_title=self.source_title,
                          source_site=self.source_site,
                          book_subject=self.subject)

        self._copy_file('mimetype', 'stylesheet.css', "META-INF/container.xml")
        base.download(self.cover, os.path.join(self.novel_dir, "cover.jpg"))
        base.make_zip(self.novel_dir, "./novel/%s.epub" % self.name)

    def _make_mobi(self):
        file_name = "./novel/%s.epub" % self.name
        tool_file = './tool/kindlegen.exe'
        if not os.path.exists(file_name):
            return
        if not os.path.exists(tool_file):
            return

        print("开始生成Mobi电子书...")
        try:
            pipe = subprocess.Popen(
                [os.path.abspath(tool_file), file_name],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)
            pipe.communicate()
        except Exception as error:
            print(error)

    def _copy_file(self, *file_names):
        for name in file_names:
            shutil.copy("./epub_temple/%s" % name,
                        os.path.join(self.novel_dir, name))

    def _get_time(self):
        import time
        return time.asctime(time.localtime(time.time()))

    def _make_temple(self, in_file_name, out_file_name=None, **temple_args):
        if not out_file_name:
            out_file_name = in_file_name
        with open("./epub_temple/%s" % in_file_name, encoding="utf-8") as in_file:
            temple = in_file.read()
            out_file_content = string.Template(temple).substitute(temple_args)
            with open(os.path.join(self.novel_dir, out_file_name), "w+", encoding="utf-8") as out_file:
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
        with self.lock:
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
