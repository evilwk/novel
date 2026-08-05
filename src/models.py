# -*- coding: utf-8 -*-
"""跨模块共享的数据结构"""

from typing import TypedDict


class Chapter(TypedDict):
    """章节"""

    index: int
    url: str
    name: str | None


class BookInfo(TypedDict):
    """书籍信息"""

    cover: str | None
    book_id: int
    author: str | None
    book_subject: str | None
    book_url: str
