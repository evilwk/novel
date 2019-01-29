import os
import string
import time
import utils

template_container = """<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>"""

template_content = """<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="zh-CN">
<head><title>${chapter_title}</title><meta http-equiv="Content-Type" content="text/html; charset=utf-8" /><link href="stylesheet.css" type="text/css" rel="stylesheet" /><style type="text/css">@page { margin-bottom: 5pt; margin-top: 5pt; }</style></head>
<body>
<h2>${chapter_title}</h2>
<div class="content">
${chapter_content}
</div>
</body>
</html>"""

template_content_opf = """<?xml version="1.0" encoding="utf-8"?>

<package xmlns="http://www.idpf.org/2007/opf" xmlns:dc="http://purl.org/dc/elements/1.1/" unique-identifier="bookid" version="2.0">
  <metadata xmlns:opf="http://www.idpf.org/2007/opf">
    <dc:title>${book_title}</dc:title>
    <dc:identifier id="book_id">${book_id}</dc:identifier>
    <dc:creator>${author}</dc:creator>
    <dc:language>zh-CN</dc:language>
    <dc:date>${create_time}</dc:date>
    <dc:contributor>${source_title}</dc:contributor>
    <dc:publisher>${source_title}, ${source_site}</dc:publisher>
    <dc:subject>${book_subject}</dc:subject>
    <dc:rights>Copyright (C) 2002-2008 ${source_site}</dc:rights>
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

template_mimetype = "application/epub+zip"

template_stylesheet = """h2 { text-align: center; page-break-before: always; font-weight: bold; border-bottom: dotted 2px Red; }
a { color: blue; text-decoration: underline; }
.cover { padding: 20px; text-align: center; }
.cover img { border: solid #CCC 1px; padding: 3px; }
.cover img:hover { background: #EFEFEF; }
.bookinfo ul { padding: 5px; margin: 0px; list-style-type: none; border: solid #CCC 1px; margin-bottom: 6px; }
.bookinfo ul li { padding: 5px; margin: 0px; border-bottom: dotted #CCC 1px; }
.bookinfo ul li pre { margin-left: 30px; word-wrap: break-word; word-break: break-all; }"""

template_title = """<?xml version='1.0' encoding='utf-8' ?>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="zh-CN"><head><title>封面</title><meta http-equiv="Content-Type" content="text/html; charset=utf-8" /><link href="stylesheet.css" type="text/css" rel="stylesheet" /><style type="text/css">@page { margin-bottom: 5pt; margin-top: 5pt; }</style></head>
<body>
<div class="cover">
<a href="${book_link}" target="_blank" title="访问《${book_title}》官方页面"><img src="cover.jpg" alt="${book_title}" /></a>
</div>
<div class="bookinfo">
<ul>
<li><b>书名</b>：<a href="${book_link}" target="_blank" title="访问《${book_title}》官方页面">${book_title}</a></li>
<li><b>主题</b>：${book_subject}</li>
</ul>
<ul><li><b>${source_title}</b>：<a href="${source_site}" target="_blank">${source_site}</a></li></ul>
</div>
</body>
</html>"""

template_toc_ncx = """<?xml version='1.0' encoding='utf-8'?>
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

nav_point_temple = """        <navPoint id="{0}" playOrder="{1}">
            <navLabel>
                <text>{2}</text>
            </navLabel>
            <content src="{0}.html"/>
        </navPoint>"""

manifest_item_temple = '    <item id="{0}" href="{0}.html" media-type="application/xhtml+xml"/>'

spine_item_temple = '    <itemref idref="{0}"/>'


def get_time():
    return time.asctime(time.localtime(time.time()))


def make_zip(source_dir, output_filename):
    import os
    import zipfile
    if not os.path.isabs(source_dir):
        source_dir = os.path.abspath(source_dir)
    with zipfile.ZipFile(output_filename, 'w') as zip_file:
        for parent, dirnames, filenames in os.walk(source_dir):
            for filename in filenames:
                file_path = os.path.join(parent, filename)
                arc_name = file_path.replace(source_dir, "").strip(os.path.sep)
                zip_file.write(file_path, arc_name)


class EPub:
    def __init__(self, name, source_title="", source_site=""):
        self.name = name
        self.source_title = source_title  # 网站标题
        self.source_site = source_site  # 网站地址
        self.chapter_list = []

        self._save_dir = os.path.join("./epub", self.name)
        if not os.path.exists(self._save_dir):
            os.makedirs(os.path.join(self._save_dir, "META-INF"))

    def chapter_file_name(self, title):
        chapter = {'index': len(self.chapter_list), 'title': title}
        self.chapter_list.append(chapter)
        return "chapter_%d.html" % chapter["index"]

    def exists(self, file_name):
        return os.path.exists(os.path.join(self._save_dir, file_name))

    def chapter(self, file_name, title, content):
        self._make_temple(template_content, file_name, {
            'chapter_title': title,
            'chapter_content': content
        })

    def make(self, info):
        # content.opf
        manifest = []
        spine = []
        # toc
        nav = []

        nav_index = 2
        for i in range(len(self.chapter_list)):
            chapter = self.chapter_list[i]
            file_id = "chapter_%d" % chapter["index"]
            manifest.append(manifest_item_temple.format(file_id))
            spine.append(spine_item_temple.format(file_id))
            nav.append(
                nav_point_temple.format(file_id, nav_index, chapter["title"]))
            nav_index += 1

        info["source_title"] = self.source_title
        info["source_site"] = self.source_site
        info["book_title"] = self.name
        info["create_time"] = get_time()
        info["manifest_item"] = "\n".join(manifest)
        info["spine_item"] = "\n".join(spine)
        info["nav_point"] = '\n'.join(nav)

        self._make_temple(template_content_opf, "content.opf", info)
        self._make_temple(template_toc_ncx, "toc.ncx", info)
        self._make_temple(template_title, "title.xhtml", info)

        self._write_template(template_mimetype, 'mimetype')
        self._write_template(template_stylesheet, 'stylesheet.css')
        self._write_template(template_container, 'META-INF/container.xml')

        utils.download(info['cover'], os.path.join(self._save_dir, "cover.jpg"))
        epub_file_name = "./epub/%s.epub" % self.name
        make_zip(self._save_dir, epub_file_name)
        return epub_file_name

    def _make_temple(self, template, file_name=None, temple_args=None):
        if temple_args is None:
            temple_args = {}
        with open(os.path.join(self._save_dir, file_name), "w+", encoding="utf-8") as out_file:
            out_file.write(string.Template(template).substitute(**temple_args))

    def _write_template(self, template, file_name):
        with open(os.path.join(self._save_dir, file_name), "w+", encoding='utf-8') as file:
            file.write(template)
