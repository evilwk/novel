# coding:utf-8
import os
import re
import subprocess

import requests
from requests.adapters import HTTPAdapter


def match(text, *patterns):
    """匹配正则表达式的第一个结果"""
    if len(patterns) == 1:
        pattern = patterns[0]
        m = re.search(pattern, text)
        if m:
            return m.group(1)
        else:
            return None
    else:
        ret = []
        for pattern in patterns:
            m = re.search(pattern, text)
            if m:
                ret.append(m.group(1))
        return ret


def get_html(url, headers=None, encode=None):
    if headers is None:
        headers = {}
    session = requests.Session()
    session.mount('http://', HTTPAdapter(max_retries=3))
    session.mount('https://', HTTPAdapter(max_retries=3))

    response = session.get(url, headers=headers)
    if encode:
        response.encoding = encode
    return response.text


def download(url, file_name, headers=None):
    if headers is None:
        headers = {}

    headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)" \
                            " Chrome/64.0.3282.140 Safari/537.36 Edge/17.17134"

    session = requests.Session()
    session.mount('http://', HTTPAdapter(max_retries=3))
    session.mount('https://', HTTPAdapter(max_retries=3))

    response = session.get(url, headers=headers)
    with open(file_name, "wb+") as file:
        file.write(response.content)


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


def is_mac_os():
    import platform
    return platform.system() == "Darwin"


def get_usable_cmd():
    try:
        p = subprocess.Popen(
            ['kindlegen'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out, err = p.communicate()
        version = match(out.decode('utf-8'), r"V(\d.\d)\sbuild")
        if version:
            return True
    except Exception as error:
        pass
    return False


def make_mobi(epub_file_name):
    tool_file = os.path.abspath('./tool/kindlegen.exe')
    if not os.path.exists(epub_file_name):
        return

    if is_mac_os():
        if get_usable_cmd():
            tool_file = "kindlegen"
        else:
            print("使用brew安装kindlegen")
            return
    elif not os.path.exists(tool_file):
        return

    print("开始生成Mobi电子书...")
    try:
        pipe = subprocess.Popen(
            [tool_file, epub_file_name, "-dont_append_source"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        pipe.communicate()
    except Exception as error:
        print(error)
