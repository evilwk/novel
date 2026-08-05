# -*- coding: utf-8 -*-
"""EPub 用到的静态模板"""

CONTAINER = """<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>"""

CONTENT = """<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="zh-CN">
<head><title>${chapter_title}</title><meta http-equiv="Content-Type" content="text/html; charset=utf-8" /><link href="stylesheet.css" type="text/css" rel="stylesheet" /><style type="text/css">@page { margin-bottom: 5pt; margin-top: 5pt; }</style></head>
<body>
<h2>${chapter_title}</h2>
<div class="content">
${chapter_content}
</div>
</body>
</html>"""

CONTENT_OPF = """<?xml version="1.0" encoding="utf-8"?>

<package xmlns="http://www.idpf.org/2007/opf" xmlns:dc="http://purl.org/dc/elements/1.1/" unique-identifier="bookid" version="2.0">
  <metadata xmlns:opf="http://www.idpf.org/2007/opf">
    <dc:title>${book_title}</dc:title>
    <dc:identifier id="book_id">${book_id}</dc:identifier>
    <dc:creator>${author}</dc:creator>
    <dc:language>zh-CN</dc:language>
    <dc:date>${create_time}</dc:date>
    <dc:contributor>${site_name}</dc:contributor>
    <dc:publisher>${site_name}, ${site_url}</dc:publisher>
    <dc:subject>${book_subject}</dc:subject>
    <dc:rights>Copyright (C) 2002-2008 ${site_url}</dc:rights>
    <meta name="cover" content="cover-image"/>
  </metadata>
  <manifest>
    <item id="ncx" href="toc.ncx" media-type="application/x-dtbncx+xml"/>
    <item id="stylesheet" href="stylesheet.css" media-type="text/css"/>
    <item id="cover-image" href="cover.jpg" media-type="image/jpeg"/>
    <item id="title-page" href="title.xhtml" media-type="application/xhtml+xml"/>
${manifest_item}
  </manifest>
  <spine toc="ncx">
    <itemref idref="title-page"/>
${spine_item}
  </spine>
  <guide>
    <reference href="title.xhtml" type="title-page" title="书籍信息"/>
  </guide>
</package>"""

MIMETYPE = "application/epub+zip"

STYLESHEET = """h2 { text-align: center; page-break-before: always; font-weight: bold; border-bottom: dotted 2px Red; }
a { color: blue; text-decoration: underline; }
.cover { padding: 20px; text-align: center; }
.cover img { border: solid #CCC 1px; padding: 3px; }
.cover img:hover { background: #EFEFEF; }
.bookinfo ul { padding: 5px; margin: 0px; list-style-type: none; border: solid #CCC 1px; margin-bottom: 6px; }
.bookinfo ul li { padding: 5px; margin: 0px; border-bottom: dotted #CCC 1px; }
.bookinfo ul li pre { margin-left: 30px; word-wrap: break-word; word-break: break-all; }"""

TITLE = """<?xml version='1.0' encoding='utf-8' ?>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="zh-CN"><head><title>封面</title><meta http-equiv="Content-Type" content="text/html; charset=utf-8" /><link href="stylesheet.css" type="text/css" rel="stylesheet" /><style type="text/css">@page { margin-bottom: 5pt; margin-top: 5pt; }</style></head>
<body>
<div class="cover">
<a href="${book_url}" target="_blank" title="访问《${book_title}》官方页面"><img src="cover.jpg" alt="${book_title}" /></a>
</div>
<div class="bookinfo">
<ul>
<li><b>书名</b>：<a href="${book_url}" target="_blank" title="访问《${book_title}》官方页面">${book_title}</a></li>
<li><b>主题</b>：${book_subject}</li>
</ul>
<ul><li><b>${site_name}</b>：<a href="${site_url}" target="_blank">${site_url}</a></li></ul>
</div>
</body>
</html>"""

TOC_NCX = """<?xml version='1.0' encoding='utf-8'?>
<ncx
    xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
    <head>
        <meta content="${book_id}" name="dtb:uid"/>
        <meta content="1" name="dtb:depth"/>
        <meta content="0" name="dtb:totalPageCount"/>
        <meta content="0" name="dtb:maxPageNumber"/>
    </head>
    <navMap>
        <navPoint id="title-page" playOrder="1">
            <navLabel>
                <text>书籍信息</text>
            </navLabel>
            <content src="title.xhtml"/>
        </navPoint>
${nav_point}
    </navMap>
</ncx>"""

NAV_POINT = """        <navPoint id="{0}" playOrder="{1}">
            <navLabel>
                <text>{2}</text>
            </navLabel>
            <content src="{0}.html"/>
        </navPoint>"""

MANIFEST_ITEM = '    <item id="{0}" href="{0}.html" media-type="application/xhtml+xml"/>'

SPINE_ITEM = '    <itemref idref="{0}"/>'
