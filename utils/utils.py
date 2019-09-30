# -*- coding: utf-8 -*-

import os
import re
import subprocess

import requests
from requests.adapters import HTTPAdapter

from .config import *


def match(text, *patterns):
    """匹配正则表达式的第一个结果"""
    if len(patterns) == 1:
        pattern = patterns[0]
        m = re.search(pattern, text, re.DOTALL)
        if m:
            return m.group(1)
        else:
            return None
    else:
        ret = []
        for pattern in patterns:
            m = re.search(pattern, text, re.DOTALL)
            if m:
                ret.append(m.group(1))
        return ret


def get_response(url, **kwargs):
    session = requests.Session()
    session.mount('http://', HTTPAdapter(max_retries=3))
    session.mount('https://', HTTPAdapter(max_retries=3))

    if "headers" not in kwargs:
        kwargs["headers"] = {}
    if "User-Agent" not in kwargs["headers"]:
        kwargs["headers"][
            "User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)" \
                            " Chrome/64.0.3282.140 Safari/537.36 Edge/17.17134"

    proxies, timeout = None, None
    if "proxies" in kwargs:
        proxies = kwargs["proxies"]
        del kwargs["proxies"]
    else:
        proxy = get_network_proxy()
        # http://  socks5h://
        if len(proxy) >= 10:
            proxies = {"http": proxy, "https": proxy}

    if "timeout" in kwargs:
        timeout = kwargs["timeout"]
        del kwargs["timeout"]
    else:
        timeout = get_network_timeout()

    try:
        requests.packages.urllib3.disable_warnings()
        return session.get(url,
                           proxies=proxies,
                           verify=False,
                           timeout=timeout,
                           **kwargs)
    except Exception as error:
        print("request %s %s" % (url, str(error)))
        return None


def get_html(url, encoding=None, **kwargs):
    response = get_response(url, **kwargs)
    if response:
        if encoding:
            response.encoding = encoding
        return response.text
    else:
        return ""


def download(url, file_name, **kwargs):
    response = get_response(url, **kwargs)
    if response:
        with open(file_name, "wb+") as file:
            file.write(response.content)
        return True
    else:
        return False


def is_mac_os():
    import platform
    return platform.system() == "Darwin"


def get_usable_cmd():
    try:
        p = subprocess.Popen(['kindlegen'],
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        out, err = p.communicate()
        version = match(out.decode('utf-8'), r"V(\d.\d)\sbuild")
        if version:
            return True
    except Exception:
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
