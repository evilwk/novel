import os

from bs4 import BeautifulSoup

import utils


class BaseNovel:
    _encoding = "utf-8"

    id = ""
    name = ""
    cover = ""  # 封面
    author = "Unkown"
    subject = "Unkown"  # 分类

    source_title = ""
    source_site = ""

    read_link = ""  # 阅读页链接
    chapter_list = []  # 章节列表 {link: "", title: ""}

    def __init__(self, novel_link, max_thread=10):
        self.novel_link = novel_link
        self._chapter_line_filters = self.chapter_line_filters()
        self._downloader = utils.Downloader(
            max_thread=max_thread, finish_func=self._download_finish)

    def __call__(self):
        # 解析基础信息
        intro_page = utils.get_html(self.novel_link, encoding=self._encoding)
        self.parse_base_info(intro_page)
        self.epub = utils.EPub(self.name, self.source_title, self.source_site)

        # 解析章节列表
        if self.read_link is None or self.read_link == '':
            print("没有小说目录页面")
            return

        if self.read_link == self.novel_link:
            self.parse_chapter_list(intro_page)
        else:
            read_page = base.get_html(self.read_link, encode=self._encoding)
            self.parse_chapter_list(read_page)

        if not self.chapter_list:
            print("章节列表为空")
            return
        print("%s 作者:%s 共%d章" % (self.name, self.author,
                                 len(self.chapter_list)))
        for chapter in self.chapter_list:
            self._downloader.submit(self._download_chapter_content, chapter)

        self._downloader.start()

    def _download_finish(self):
        print("")
        print("《%s》下载完成" % self.name)
        info = {
            'cover': self.cover,
            'book_id': self.id,
            'author': self.author,
            'book_subject': self.subject,
            'book_link': self.novel_link
        }
        epub_file_name = self.epub.make(info)
        print(os.path.abspath(epub_file_name))
        utils.make_mobi(epub_file_name)

    def _download_chapter_content(self, chapter):
        chapter_file_name = self.epub.chapter_file_name(chapter["title"])
        if not self.epub.exists(chapter_file_name):
            content_page = utils.get_html(chapter["link"], encoding=self._encoding)
            novel_chapter = self._parse_chapter_content(chapter, content_page)
            self.epub.chapter(chapter_file_name, chapter["title"], novel_chapter)

    def parse_base_info(self, content):
        """解析基础信息"""
        pass

    def parse_chapter_list(self, content):
        """解析章节列表"""
        pass

    @staticmethod
    def chapter_soup_select():
        """章节内容选择器"""
        pass

    def _parse_chapter_content(self, chapter, content_page):
        soup = BeautifulSoup(content_page, "html.parser")
        try:
            item = soup.select(self.chapter_soup_select())[0]
        except Exception as error:
            print(chapter["link"], error)
            return

        lines = []
        for line in item.stripped_strings:
            strip_line = line.strip()
            if strip_line == "" or self._filter_line(strip_line):
                continue
            lines.append("<p>　　%s</p>" % strip_line)
        return "\n".join(lines)

    def _filter_line(self, line):
        for item in self._chapter_line_filters:
            if item in line:
                return True
        return False

    @staticmethod
    def chapter_line_filters():
        return []
