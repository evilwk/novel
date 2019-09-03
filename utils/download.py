# -*- coding: utf-8 -*-

import queue
import sys
import threading
import time


class ThreadSafeCounter:
    def __init__(self):
        self._lock = threading.Lock()
        self._value = 0

    def increment(self):
        with self._lock:
            self._value += 1

    def decrement(self):
        with self._lock:
            self._value -= 1

    @property
    def value(self):
        with self._lock:
            return self._value

    @value.setter
    def value(self, v):
        with self._lock:
            self._value = v


DEFAULT_PROGRESS_LEN = 20


class Downloader:
    _queue = queue.Queue()
    _threads = []

    _download_complete = ThreadSafeCounter()
    _download_count = 0
    _percent_func = None
    _finish_func = None
    _kill = False

    def __init__(self, max_thread=10, percent_func=None, finish_func=None):
        self._max_thread = max_thread

        self._percent_func = percent_func
        self._finish_func = finish_func
        self._lock = threading.Lock()

    def submit(self, func, arg):
        self._download_count += 1
        self._queue.put((func, arg))

    @staticmethod
    def has_live_threads(threads):
        return True in [t.is_alive() for t in threads]

    def start(self):
        threads = []
        for i in range(self._max_thread):
            thread = threading.Thread(target=self._download,
                                      name="download:%d" % i)
            thread.start()
            threads.append(thread)

        while self.has_live_threads(threads):
            try:
                [t.join(1) for t in threads if t is not None and t.is_alive()]
            except KeyboardInterrupt:
                print("downloader break")
                self._kill = True
                return

        if self._finish_func:
            self._finish_func()

    def _download(self):
        while not self._kill and not self._queue.empty():
            (func, arg) = self._queue.get()
            func(arg)

            if self._percent_func:
                self._percent_func()
            else:
                self._default_percent()

    def _default_percent(self):
        self._download_complete.increment()
        with self._lock:
            value = self._download_complete.value
            percent = value * 1.0 / self._download_count * 100
            done = int(value / self._download_count * DEFAULT_PROGRESS_LEN)
            sys.stdout.write(
                '%d/%d %.2f%% [%s%s]\r' %
                (value, self._download_count, percent, '#' * done, '-' *
                 (DEFAULT_PROGRESS_LEN - done)))
            sys.stdout.flush()
            time.sleep(0.01)
