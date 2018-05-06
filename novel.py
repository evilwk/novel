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
    parser.add_option(
        "-t", "--thread", dest="thread", type="int", help="set thread count")
    return parser.parse_args()


def main():
    (options, urls) = parse_arg()
    for url in urls:
        domain = base.get_url_tld(url)
        if domain in config.keys():
            if options.thread:
                novel = config[domain](url, max_thread=options.thread)
            else:
                novel = config[domain](url)
            novel()
        else:
            print("don't support %s" % url)


if __name__ == '__main__':
    main()
