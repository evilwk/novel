# -*- coding: utf-8 -*-

import argparse
import json
import os
import urllib.parse as urlparse

from bs4 import BeautifulSoup

import utils
from utils import EPub

BIQUGE_RULE_NAME = "re:<meta\\s+property=\"og:novel:book_name\"\\s+content=\"(.*?)\"\\s*/>"
BIQUGE_RULE_COVER = "re:<meta\\s+property=\"og:image\"\\s+content=\"(.*?)\"\\s*/>"
BIQUGE_RULE_AUTHOR = "re:<meta\\s+property=\"og:novel:author\"\\s+content=\"(.*?)\"\\s*/>"
BIQUGE_RULE_CATEGORY = "re:<meta\\s+property=\"og:novel:category\"\\s+content=\"(.*?)\"\\s*/>"


class AnalyzeRule:
    def __init__(self, site_rule, content, element):
        self._site_rule = site_rule
        self._content = content
        self._element = element

    @staticmethod
    def _is_re(rule):
        return rule.startswith("re:")

    @staticmethod
    def _get_rule(rule):
        if AnalyzeRule._is_re(rule):
            return rule[3:]
        return rule.split("@")

    @staticmethod
    def _get_attr(element, name):
        if name == "text":
            return element.get_text()

        return element[name]

    def get_elements(self, rule_name):
        rule = self._site_rule[rule_name]
        if not rule:
            return
        rules = self._get_rule(rule)
        if not rules:
            return

        return self._element.select(rules[0])

    def get_element(self, rule_name):
        elements = self.get_elements(rule_name)
        if not elements:
            return

        return elements[0]

    def get_text(self, rule_name, default=None):
        rule = self._site_rule[rule_name]
        if not rule:
            return default
        if self._is_re(rule):
            return self.get_re_text(rule)
        else:
            texts = self.get_texts(rule_name)
            if texts:
                return texts[0]

    def get_re_text(self, rule):
        return utils.match(self._content, self._get_rule(rule))

    def get_texts(self, rule_name):
        elements = self.get_elements(rule_name)
        if not elements:
            return

        texts = []
        rules = self._get_rule(self._site_rule[rule_name])
        if len(rules) > 1:
            for element in elements:
                try:
                    text = self._get_attr(element, rules[1])
                    texts.append(text)
                except Exception:
                    pass

        return texts


class NovelRule(object):
    def __init__(self, site_rule):
        self._site_rule = site_rule

    def __getattr__(self, name):
        if name not in self._site_rule:
            return None

        v = self._site_rule[name]
        if isinstance(v, dict):
            return dict(v)
        if isinstance(v, list):
            r = []
            for i in v:
                r.append(i)
            return r
        else:
            return self._site_rule[name]

    def __getitem__(self, name):
        if name not in self._site_rule:
            return None
        return self._site_rule[name]


class NovelEngine:
    id = ""
    name = ""
    cover = ""  # 封面
    author = ""
    category = ""  # 分类

    _epub = None
    _site_rule = None

    def __init__(self, novel_url, max_thread=10):
        self._url = novel_url
        if not max_thread:
            max_thread = 10
        self._downloader = utils.Downloader(max_thread=max_thread,
                                            finish_func=self._download_finish)

    def _load_rule(self):
        rules = []
        with open("novel.json", "rb") as file:
            json_rules = json.load(file)  # list
            for rule in json_rules:
                rules.append(NovelRule(rule))

        if not rules:
            print("规则加载失败")
            exit()

        hostname = urlparse.urlparse(self._url).hostname
        for rule in rules:
            site_url = rule.siteUrl or ""
            if urlparse.urlparse(site_url).hostname == hostname:
                self._site_rule = rule
                break

        if not self._site_rule:
            print("找不到%s站点规则" % self._url)
            exit()

    def _charset(self):
        return self._site_rule.charset or "utf-8"

    def _get_analyzer(self, content, element):
        return AnalyzeRule(self._site_rule, content, element)

    def start(self):
        # 加载规则
        self._load_rule()

        # 解析基础信息
        basic_content = utils.get_html(self._url, encoding=self._charset())
        basic_soup = BeautifulSoup(basic_content, "html.parser")

        basic_analyzer = self._get_analyzer(basic_content, basic_soup)
        self.id = 0
        if self._site_rule["isBiquge"]:
            self.name = basic_analyzer.get_re_text(BIQUGE_RULE_NAME)
            self.cover = basic_analyzer.get_re_text(BIQUGE_RULE_COVER)
            self.author = basic_analyzer.get_re_text(BIQUGE_RULE_AUTHOR)
            self.category = basic_analyzer.get_re_text(BIQUGE_RULE_CATEGORY)
        else:
            self.name = basic_analyzer.get_text("ruleName")
            self.cover = basic_analyzer.get_text("ruleCover")
            self.author = basic_analyzer.get_text("ruleAuthor")
            self.category = basic_analyzer.get_text("ruleCategory")

        self._epub = utils.EPub(self.name, self._site_rule.siteName,
                                self._site_rule.siteUrl)
        # 解析目录
        self._analyze_chapters(basic_analyzer)

    def _analyze_chapters(self, basic_ayalyzer):
        chapters_url = basic_ayalyzer.get_text("ruleChapterUrl")

        # 准备章节内容
        chapters_analyzer = None
        if not chapters_url:
            chapters_analyzer = basic_ayalyzer
        else:
            content = utils.get_html(chapters_url, encoding=self._charset())
            soup = BeautifulSoup(content, "html.parser")
            chapters_analyzer = self._get_analyzer(content, soup)

        # 分析章节列表
        chapers_items = chapters_analyzer.get_elements("ruleChapterItems")
        index = 0
        chapters = []
        for chapter_item in chapers_items:
            item_text = str(chapter_item)
            analyzer = self._get_analyzer(item_text, chapter_item)
            name = analyzer.get_text("ruleChapterName")
            content_url = analyzer.get_text("ruleContentUrl")
            # yapf: disable
            chapters.append({
                'index': index,
                'url': urlparse.urljoin(self._url, content_url),
                'name': name
            })
            # yapf: enable
            index += 1

        if not chapters:
            print("章节列表为空")
            exit()

        print("%s 作者:%s 共%d章" % (self.name, self.author, len(chapters)))
        for chapter in chapters:
            self._downloader.submit(self._download_chapter, chapter)

        self._downloader.start()

    def _download_chapter(self, chapter):
        file_name = self._epub.chapter_file_name(chapter["name"])
        if not self._epub.exists(file_name):
            content_page = utils.get_html(chapter["url"],
                                          encoding=self._charset())
            chapter_content = self._analyze_chapter(chapter, content_page)
            self._epub.chapter(file_name, chapter["name"], chapter_content)

    def _download_finish(self):
        print("")
        print("《%s》下载完成" % self.name)
        info = {
            'cover': self.cover,
            'book_id': self.id,
            'author': self.author,
            'book_subject': self.category,
            'book_url': self._url
        }
        epub_file_name = self._epub.make(info)
        print(os.path.abspath(epub_file_name))
        utils.make_mobi(epub_file_name)

    def _analyze_chapter(self, chapter, content):
        soup = BeautifulSoup(content, "html.parser")
        analyzer = self._get_analyzer(content, soup)
        element = analyzer.get_element("ruleChapterContent")
        if not element:
            print("%s章节解析错误" % chapter["url"])
            return ""

        lines = []
        ignore_lines = self._site_rule.ruleIgnoreLines
        for line in element.stripped_strings:
            strip_line = line.strip()
            if strip_line == "" or self._ignore_line(ignore_lines, strip_line):
                continue
            lines.append("<p>　　%s</p>" % strip_line)
        return "\n".join(lines)

    @staticmethod
    def _ignore_line(ignore_lines, line):
        if not ignore_lines:
            return False
        for ignore_line in ignore_lines:
            if ignore_line in line:
                return True
        return False


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('url', nargs=1)
    parser.add_argument("--thread", default=10, type=int)
    return parser.parse_args()


if __name__ == "__main__":
    args = get_args()
    url = args.url[0]
    engine = NovelEngine(url, max_thread=args.thread)
    engine.start()
