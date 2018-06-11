#!/usr/bin/env python
# coding=utf-8

import os
import hashlib
import logging
from queue import Queue

import requests
from gevent import monkey, sleep
from gevent.pool import Pool

# Do all of the default monkey patching (calls every other applicable
# function in this module).
monkey.patch_all()


POOL_MAXSIZE = 512
WORKERS_MAXSIZE = 16
DELAY_TIME = 0.25
REQUEST_TIMEOUT = 8
MAX_RETRIES = 5

URLS_DATA = "data.txt"
PICS_DIR = "pics"
PICS_EXT = ".jpg"
PICS_FILENAME_LENGTH = 16
LOG_LEVEL = logging.WARNING

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36"
)

DOMAIN = {"mzitu": "http://i.meizitu.net/", "mmjpg": "http://img.mmjpg.com/"}

HEADERS = {
    DOMAIN["mzitu"]: {"User-Agent": USER_AGENT, "Referer": "http://www.mzitu.com"},
    DOMAIN["mmjpg"]: {"User-Agent": USER_AGENT, "Referer": "http://www.mmjpg.com"},
}


class Logger:

    @staticmethod
    def get():
        formatter = logging.Formatter("%(asctime)s - %(message)s")
        logger = logging.getLogger("monitor")
        logger.setLevel(LOG_LEVEL)

        sh = logging.StreamHandler()
        sh.setFormatter(formatter)
        logger.addHandler(sh)
        return logger


class Downloader:

    def __init__(self):
        self.urls_queue = Queue()
        self.pool = Pool(POOL_MAXSIZE)
        self.logger = Logger.get()
        self.init_queue()
        self.create_dir()

    def init_queue(self):
        with open(URLS_DATA, "r", encoding="utf8") as f:
            for u in f.readlines():
                self.urls_queue.put({u.strip(): MAX_RETRIES})

    @staticmethod
    def create_dir():
        if not os.path.exists(PICS_DIR):
            os.mkdir(PICS_DIR)

    @staticmethod
    def headers(url):
        if url.startswith(DOMAIN["mzitu"]):
            return HEADERS.get(DOMAIN["mzitu"])
        if url.startswith(DOMAIN["mmjpg"]):
            return HEADERS.get(DOMAIN["mmjpg"])

    def download(self):
        while True:
            sleep(DELAY_TIME)
            for url, num in self.urls_queue.get().items():
                self.logger.warning("Jobs " + str(self.urls_queue.qsize()))
                if num <= 0:
                    # For each get() used to fetch a task, a subsequent call
                    # to task_done() tells the queue that the processing on
                    # the task is complete.
                    self.urls_queue.task_done()
                    break
                try:
                    file_name = hashlib.sha224(url.encode("utf8")).hexdigest()[
                        :PICS_FILENAME_LENGTH
                    ] + PICS_EXT
                    file_path = os.path.join(PICS_DIR, file_name)
                    if os.path.exists(file_path):
                        self.urls_queue.task_done()
                        self.logger.warning("Ignore {} has existed".format(file_path))
                        break
                    resp = requests.get(
                        url, headers=self.headers(url), timeout=REQUEST_TIMEOUT
                    )
                    with open(file_path, "wb") as f:
                        f.write(resp.content)
                        self.logger.info("Filename " + file_name)
                    self.urls_queue.task_done()
                except Exception as e:
                    self.logger.error(e)
                    if num >= 1:
                        self.urls_queue.task_done()
                        self.urls_queue.put({url: num - 1})
                        self.logger.warning(
                            "Url {} retry times {}".format(url, MAX_RETRIES - (num - 1))
                        )

    def execute_jobs(self, target):
        for i in range(WORKERS_MAXSIZE):
            self.pool.apply_async(target)

    def run(self):
        self.execute_jobs(self.download)
        # If a join() is currently blocking, it will resume when all items
        # have been processed (meaning that a task_done() call was received
        # for every item that had been put() into the queue).
        self.urls_queue.join()


if __name__ == "__main__":
    try:
        downloader = Downloader()
        downloader.run()
    except KeyboardInterrupt:
        print("You have canceled all jobs.")
