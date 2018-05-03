# coding:utf-8

from optparse import OptionParser

import utils.base as base
from sites import *

config = {
    "txtjia.com": TxtJia,
    "qu.la": Qu,
    "biquge.com.tw": Biquge,
    "biqubook.com": Biqubook,
    "booktxt.net": Booktxt
}


def parse_arg():
    parser = OptionParser()
    parser.add_option("-t", "--thread", dest="thread", type="int", help="set thread count")
    return parser.parse_args()


def wait_exit():
    import msvcrt
    msvcrt.getch()
    exit()


def main():
    print("提示：按任意键结束运行\n")

    (options, urls) = parse_arg()
    # download only
    if len(urls) > 0:
        url = urls[0]
        domain = base.get_url_tld(url)
        if domain in config.keys():
            if options.thread:
                novel = config[domain](url, max_thread=options.thread)
            else:
                novel = config[domain](url)
            novel()
        wait_exit()


if __name__ == '__main__':
    main()
