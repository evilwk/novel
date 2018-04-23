# coding:utf-8
import re
from tld import get_tld
import requests
from requests.adapters import HTTPAdapter


def match(text, *patterns):
    """匹配正则表达式的第一个结果"""
    if len(patterns) == 1:
        pattern = patterns[0]
        match = re.search(pattern, text)
        if match:
            return match.group(1)
        else:
            return None
    else:
        ret = []
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                ret.append(match.group(1))
        return ret


def get_html(url, headers={}, encode=None):
    session = requests.Session()
    session.mount('http://', HTTPAdapter(max_retries=3))
    session.mount('https://', HTTPAdapter(max_retries=3))

    response = session.get(url, headers=headers)
    if encode:
        response.encoding = encode
    return response.text


def download(url, file_name, headers={}):
    session = requests.Session()
    session.mount('http://', HTTPAdapter(max_retries=3))
    session.mount('https://', HTTPAdapter(max_retries=3))

    response = session.get(url, headers=headers)
    with open(file_name, "wb+") as file:
        file.write(response.content)


def get_url_domain(url):
    """获取网址的域名"""
    if not url or url.strip() == '':
        return None

    res = get_tld(url, as_object=True)
    if res:
        return res.tld


def make_zip(source_dir, output_filename):
    import os, zipfile
    if not os.path.isabs(source_dir):
        source_dir = os.path.abspath(source_dir)
    with zipfile.ZipFile(output_filename, 'w') as zip_file:
        for parent, dirnames, filenames in os.walk(source_dir):
            for filename in filenames:
                file_path = os.path.join(parent, filename)
                arc_name = file_path.replace(source_dir, "").strip(os.path.sep)
                zip_file.write(file_path, arc_name)
