# -*- coding: utf-8 -*-

import string
import time
import zipfile
from collections.abc import Iterable
from pathlib import Path

from ..models import BookInfo, Chapter
from ..utils.http import download
from ..utils.paths import EPUB_DIR
from . import templates


def get_time() -> str:
    return time.asctime(time.localtime(time.time()))


def make_zip(source_dir: Path, output_file: Path) -> None:
    """打包成 epub"""
    with zipfile.ZipFile(output_file, "w") as zip_file:
        zip_file.write(source_dir / "mimetype", "mimetype", compress_type=zipfile.ZIP_STORED)

        for path in sorted(source_dir.rglob("*")):
            if not path.is_file() or path.name == "mimetype":
                continue
            arc_name = path.relative_to(source_dir).as_posix()
            zip_file.write(path, arc_name, compress_type=zipfile.ZIP_DEFLATED)


class EPub:
    def __init__(self, name: str, site_name: str = "", site_url: str = "") -> None:
        self.name = name
        self.site_name = site_name  # 网站标题
        self.site_url = site_url  # 网站地址
        # 目录顺序由抓取时的 index 决定，与章节下载完成的先后无关。
        self.chapters: list[Chapter] = []

        self._save_dir = EPUB_DIR / self.name
        (self._save_dir / "META-INF").mkdir(parents=True, exist_ok=True)

    def set_chapters(self, chapters: Iterable[Chapter]) -> None:
        """登记完整目录，chapters 需按原文顺序排列。"""
        self.chapters = list(chapters)

    @staticmethod
    def chapter_file_name(index: int) -> str:
        return "chapter_%d.html" % index

    def exists(self, file_name: str) -> bool:
        return (self._save_dir / file_name).exists()

    def chapter(self, file_name: str, title: str | None, content: str) -> None:
        self._make_temple(
            templates.CONTENT,
            file_name,
            {
                "chapter_title": title,
                "chapter_content": content,
            },
        )

    def make(self, info: BookInfo) -> Path:
        manifest: list[str] = []
        spine: list[str] = []
        nav: list[str] = []

        # playOrder 从 2 开始，1 留给书籍信息页
        for nav_index, chapter in enumerate(self.chapters, start=2):
            file_id = "chapter_%d" % chapter["index"]
            manifest.append(templates.MANIFEST_ITEM.format(file_id))
            spine.append(templates.SPINE_ITEM.format(file_id))
            nav.append(templates.NAV_POINT.format(file_id, nav_index, chapter["name"]))

        args: dict[str, object] = {
            **info,
            "site_name": self.site_name,
            "site_url": self.site_url,
            "book_title": self.name,
            "create_time": get_time(),
            "manifest_item": "\n".join(manifest),
            "spine_item": "\n".join(spine),
            "nav_point": "\n".join(nav),
        }

        self._make_temple(templates.CONTENT_OPF, "content.opf", args)
        self._make_temple(templates.TOC_NCX, "toc.ncx", args)
        self._make_temple(templates.TITLE, "title.xhtml", args)

        self._write_template(templates.MIMETYPE, "mimetype")
        self._write_template(templates.STYLESHEET, "stylesheet.css")
        self._write_template(templates.CONTAINER, "META-INF/container.xml")

        cover = info.get("cover")
        if cover and not download(cover, self._save_dir / "cover.jpg"):
            print("封面下载失败：%s" % cover)

        epub_file = EPUB_DIR / ("%s.epub" % self.name)
        make_zip(self._save_dir, epub_file)
        return epub_file

    def _make_temple(
        self,
        template: str,
        file_name: str,
        temple_args: dict[str, object] | None = None,
    ) -> None:
        text = string.Template(template).substitute(**(temple_args or {}))
        self._write_template(text, file_name)

    def _write_template(self, template: str, file_name: str) -> None:
        path = self._save_dir / file_name
        with open(path, "w+", encoding="utf-8") as file:
            file.write(template)
