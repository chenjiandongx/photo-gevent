# 美女写真图爬虫 gevent 版

## 概述

#### gevent/queue
之前写多线程/多进程爬虫一直没有用到第三方库，后来看了 gevent 的文档，觉得可以来试试。觉得还是拿妹子爬虫来试可能比较好一点，毕竟兴趣是最好的老师...

主要是使用了 gevent 的 Pool 模块，这应该是一个线程池。然后使用标准库 queue 作队列。

关于 queue 官方的介绍如下
> The queue module implements multi-producer, multi-consumer queues. It is especially useful in threaded programming when information must be exchanged safely between multiple threads.

queue 是线程安全的，也就是不存在同时读写同一个 item 的情况。在 queue 的基础上，我新增了重试限制功能，避免无限次对一个 item 进行重试。

#### 资源占用情况
> （机器配置 i7 7700 HQ + 16G RAM）

```bash
  PID USER      PR  NI    VIRT    RES    SHR S  %CPU %MEM     TIME+ COMMAND
   82 chenjia+  20   0  864420 102984  10172 S   3.3  0.6   0:08.90 python
```

可以看到，实际占用的资源是非常少的，效率是极高的。并且网速也就基本是接近满速的。

## 如何运行

#### 图片数据
图片地址数据保存在了 `data.txt`，共 17w+ 张照片，图片的数据是我从 [mmjpg](https://github.com/chenjiandongx/mmjpg) 和 [mzitu](https://github.com/chenjiandongx/mzitu) 里提取出来的。
```bash
$ wc -l data.txt
178108 data.txt
```

#### 运行代码
```bash
$ git clone https://github.com/chenjiandongx/photo-gevent.git 
$ cd photo-gevent
$ pip install -r requirements.txt # 安装依赖
$ python core.py
```

#### 断续下载
图片名是经过 hash 过的唯一值（重名的概率基本为 0），所以在任意时间 `Ctrl+C` 暂停项目后都可以随时启动继续下载，会自动跳过重名图片。大大的提高效率。 


## License

MIT [©chenjiandongx](https://github.com/chenjiandongx)
