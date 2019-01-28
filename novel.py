# coding:utf-8

import urllib.parse
from optparse import OptionParser

from sites import *

config = {
    "www.qu.la": Qu,
    "www.biquyun.com": Biquyun,
    "www.biqubook.com": Biqubook,
    "www.booktxt.net": Booktxt
}


def parse_arg():
    parser = OptionParser()
    parser.add_option(
        "-t", "--thread", dest="thread", type="int", help="set thread count")
    return parser.parse_args()


def main():
    (options, urls) = parse_arg()
    for url in urls:
        hostname = urllib.parse.urlparse(url).hostname
        if hostname and (hostname in config.keys()):
            if options.thread:
                novel = config[hostname](url, max_thread=options.thread)
            else:
                novel = config[hostname](url)
            novel()
        else:
            print("don't support %s" % url)


if __name__ == '__main__':
    main()
