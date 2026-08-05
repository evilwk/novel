# -*- coding: utf-8 -*-
"""终端输出"""

from tqdm import tqdm


def log(message: str) -> None:
    tqdm.write(message)
