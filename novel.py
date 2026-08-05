# -*- coding: utf-8 -*-
"""命令行入口，实现在 src/ 下。"""

import argparse
import sys

from src import validate
from src.engine import NovelEngine
from src.errors import NovelError


def get_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="抓取小说生成epub")
    parser.add_argument("url", nargs=1, help="小说目录页地址")
    parser.add_argument("--thread", default=10, type=int, help="并发下载线程数")
    parser.add_argument(
        "--check",
        action="store_true",
        help="只验证规则：解析书籍信息、目录和一章正文后退出",
    )
    parser.add_argument(
        "--chapter",
        default=0,
        type=int,
        help="--check 时用第几章验证正文，默认第一章",
    )
    return parser.parse_args()


def main() -> int:
    args = get_args()
    url = args.url[0]
    try:
        if args.check:
            return 1 if validate.run(url, args.chapter) else 0

        NovelEngine(url, max_thread=args.thread).start()
    except NovelError as error:
        print(error)
        return 1
    except KeyboardInterrupt:
        print("已中断")
        return 130

    return 0


if __name__ == "__main__":
    sys.exit(main())
