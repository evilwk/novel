# -*- coding: utf-8 -*-
"""笔趣阁系通用的 og:novel 元信息规则"""

NAME = 're:<meta\\s+property="og:novel:book_name"\\s+content="(.*?)"\\s*/>'
COVER = 're:<meta\\s+property="og:image"\\s+content="(.*?)"\\s*/>'
AUTHOR = 're:<meta\\s+property="og:novel:author"\\s+content="(.*?)"\\s*/>'
CATEGORY = 're:<meta\\s+property="og:novel:category"\\s+content="(.*?)"\\s*/>'
