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


class Config:

    # 线程池容量
    POOL_MAXSIZE = 512
    # worker 数量
    WORKERS_MAXSIZE = 16
    # 每次请求延迟（秒）
    DELAY_TIME = 0.25
    # 请求超时时间（秒）
    REQUEST_TIMEOUT = 8
    # 每个链接重试次数
    MAX_RETRIES = 5
    # 日志等级
    LOG_LEVEL = logging.WARNING

    URLS_DATA = "data.txt"
    PICS_DIR = "pics"
    PICS_EXT = ".jpg"
    PICS_FILENAME_LENGTH = 16

    USER_AGENT = (
        "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36"
    )

    DOMAIN = {"mzitu": "http://i.meizitu.net/", "mmjpg": "http://img.mmjpg.com/"}

    HEADERS = {
        DOMAIN["mzitu"]: {"User-Agent": USER_AGENT, "Referer": "http://www.mzitu.com"},
        DOMAIN["mmjpg"]: {"User-Agent": USER_AGENT, "Referer": "http://www.mmjpg.com"},
    }


CONFIG = Config()


class Logger:

    @staticmethod
    def get():
        formatter = logging.Formatter("%(asctime)s - %(message)s")
        logger = logging.getLogger("monitor")
        logger.setLevel(CONFIG.LOG_LEVEL)

        sh = logging.StreamHandler()
        sh.setFormatter(formatter)
        logger.addHandler(sh)
        return logger


class Downloader:

    def __init__(self):
        self.urls_queue = Queue()
        self.pool = Pool(CONFIG.POOL_MAXSIZE)
        self.logger = Logger.get()
        self.init_queue()
        self.create_dir()

    def init_queue(self):
        """
        初始化队列，导入数据
        """
        with open(CONFIG.URLS_DATA, "r", encoding="utf8") as f:
            for u in f.readlines():
                self.urls_queue.put({u.strip(): CONFIG.MAX_RETRIES})

    @staticmethod
    def create_dir():
        """
        如果文件夹不存在，则创建文件夹
        """
        if not os.path.exists(CONFIG.PICS_DIR):
            os.mkdir(CONFIG.PICS_DIR)

    @staticmethod
    def headers(url):
        """
        根据对应 url 返回 headers
        """
        if url.startswith(CONFIG.DOMAIN["mzitu"]):
            return CONFIG.HEADERS.get(CONFIG.DOMAIN["mzitu"])
        if url.startswith(CONFIG.DOMAIN["mmjpg"]):
            return CONFIG.HEADERS.get(CONFIG.DOMAIN["mmjpg"])

    def download(self):
        """
        下载图片
        """
        while True:
            sleep(CONFIG.DELAY_TIME)
            for url, num in self.urls_queue.get().items():
                # 队列大小
                self.logger.warning("Jobs: {}".format(str(self.urls_queue.qsize())))
                if num <= 0:
                    # 官方介绍
                    # For each get() used to fetch a task, a subsequent call
                    # to task_done() tells the queue that the processing on
                    # the task is complete.
                    self.urls_queue.task_done()
                    break
                try:
                    # 利用 hashlib 确保每个 url hash 成唯一的值，重新启动时可以忽略重名文件
                    file_name = hashlib.sha224(url.encode("utf8")).hexdigest()[
                        :CONFIG.PICS_FILENAME_LENGTH
                    ] + CONFIG.PICS_EXT
                    file_path = os.path.join(CONFIG.PICS_DIR, file_name)
                    if os.path.exists(file_path):
                        self.logger.warning("Ignore: {} has existed".format(file_path))
                        break
                    resp = requests.get(
                        url, headers=self.headers(url), timeout=CONFIG.REQUEST_TIMEOUT
                    )
                    with open(file_path, "wb") as f:
                        f.write(resp.content)
                        self.logger.info("Filename: {}".format(file_name))
                except Exception as e:
                    self.logger.error(e)
                    if num >= 1:
                        self.urls_queue.put({url: num - 1})
                        self.logger.warning(
                            "Url: {} retry times {}".format(url, CONFIG.MAX_RETRIES - (num - 1))
                        )
                finally:
                    # 确保最后总会执行 task_done()
                    self.urls_queue.task_done()

    def execute_workers(self, target):
        """
        启动 workers
        """
        for i in range(CONFIG.WORKERS_MAXSIZE):
            self.pool.apply_async(target)

    def run(self):
        """
        运行主函数，用于启动队列
        """
        self.execute_workers(self.download)
        # 官方介绍
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
