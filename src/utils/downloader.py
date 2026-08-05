# -*- coding: utf-8 -*-
"""并发下载"""

from collections.abc import Callable, Sequence
from concurrent.futures import ThreadPoolExecutor, as_completed

from tqdm import tqdm

type Failure[T] = tuple[T, BaseException]


def run[T](
    func: Callable[[T], object],
    items: Sequence[T],
    max_thread: int = 10,
    desc: str = "下载中",
) -> list[Failure[T]]:
    if not items:
        return []

    failures: list[Failure[T]] = []
    with ThreadPoolExecutor(max_workers=max_thread) as pool:
        futures = {pool.submit(func, item): item for item in items}
        progress = tqdm(total=len(futures), desc=desc, unit="章", ncols=70)
        try:
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as error:
                    failures.append((futures[future], error))
                progress.update(1)
        except KeyboardInterrupt:
            for future in futures:
                future.cancel()
            raise
        finally:
            progress.close()

    return failures
