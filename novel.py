# -*- coding: utf-8 -*-

import os

import urllib.parse as urlparse
import argparse

import json
import utils
import re

from bs4 import BeautifulSoup


class AnalyzeRule:
    def __init__(self, site_rule, content, element):
        self._site_rule = site_rule
        self._content = content
        self._element = element

    def _is_re(self, rule):
        return rule.startswith("re:")

    def _get_rule(self, rule):
        if self._is_re(rule):
            return rule[3:]
        return rule.split("@")

    def _get_attr(self, element, name):
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
            return utils.match(self._content, self._get_rule(rule))
        else:
            texts = self.get_texts(rule_name)
            if texts:
                return texts[0]

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
    def __init__(self, map):
        self.map = map

    def __getattr__(self, name):
        if name not in self.map:
            return (None)

        v = self.map[name]
        if isinstance(v, (dict)):
            return ((dict)(v))
        if isinstance(v, (list)):
            r = []
            for i in v:
                r.append(i)
            return (r)
        else:
            return (self.map[name])

    def __getitem__(self, name):
        if name not in self.map:
            return (None)
        return (self.map[name])


class NovelEngine:
    id = ""
    name = ""
    cover = ""  # 封面
    author = ""
    category = ""  # 分类

    _site_rule = None

    def __init__(self, url, max_thread=10):
        self._url = url
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
            url = analyzer.get_text("ruleContentUrl")
            # yapf: disable
            chapters.append({
                'index': index,
                'url': urlparse.urljoin(self._url, url),
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

    def _ignore_line(self, ignore_lines, line):
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
    print(args)
    url = args.url[0]
    engine = NovelEngine(url, max_thread=args.thread)
    engine.start()
