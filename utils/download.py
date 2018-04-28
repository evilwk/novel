import queue
import threading
import sys
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


default_progress_len = 20

class Downloader:
    _queue = queue.Queue()
    _threads = []

    _download_complete = ThreadSafeCounter()
    _download_count = 0
    _percent_func = None

    def __init__(self, max_thread=10, percent_func=None):
        self._max_thread = max_thread

        self._percent_func = percent_func
        self._lock = threading.Lock()

    def submit(self, func, arg):
        self._download_count += 1
        self._queue.put((func, arg))

    def start(self):
        for i in range(self._max_thread):
            thread = threading.Thread(target=self._download, name="download:%d" % i)
            self._threads.append(thread)
            thread.start()

    def wait(self):
        for t in self._threads:
            t.join()

    def _download(self):
        while not self._queue.empty():
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
            done = int(value / self._download_count * default_progress_len)
            sys.stdout.write('%d/%d %.2f%% [%s%s]\r' %
                             (value, self._download_count, percent, '#' * done, '.' * (default_progress_len - done)))
            sys.stdout.flush()
            time.sleep(0.01)
