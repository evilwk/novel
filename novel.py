# coding:utf-8
import sys

import base
from sites import *


def main(*urls):
    executors = {"txtjia": TxtJia}
    for url in urls:
        domain = base.get_url_domain(url)
        if domain in executors.keys():
            novel = executors[domain](url)
            novel()


if __name__ == '__main__':
    main(*sys.argv[1:])
