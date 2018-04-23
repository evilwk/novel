import queue
import threading


class Downloader():
    queue = queue.Queue()
    threads = []

    percent_func = None

    def __init__(self, max_thread=10, percent_func=None):
        self.max_thread = 10
        self.percent_func = percent_func

    def submit(self, func, arg):
        self.queue.put((func, arg))

    def start(self):
        for i in range(self.max_thread):
            thread = threading.Thread(target=self._download, name="download:%d" % i)
            self.threads.append(thread)
            thread.start()

    def wait(self):
        for t in self.threads:
            t.join()

    def _download(self):
        while not self.queue.empty():
            (func, arg) = self.queue.get()
            func(arg)
            if self.percent_func:
                self.percent_func()
