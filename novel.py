# coding:utf-8
import sys

import base
from sites import *
from optparse import OptionParser

config = {"txtjia": TxtJia, "qu": Qu}


def parse_arg():
    parser = OptionParser()
    parser.add_option("-t", "--thread", dest="thread", type="int", help="set thread count")
    return parser.parse_args()


def main():
    (options, urls) = parse_arg()
    for url in urls:
        domain = base.get_url_domain(url)
        if domain in config.keys():
            if options.thread:
                novel = config[domain](url, max_thread=options.thread)
            else:
                novel = config[domain](url)
            novel()


if __name__ == '__main__':
    main()
