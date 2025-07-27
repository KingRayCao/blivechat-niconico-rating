#!/usr/bin/env python
# -*- coding: utf-8 -*-
import asyncio
import logging.handlers
import os
import signal
import sys
from typing import *

import blcsdk
import config
import listener

logger = logging.getLogger('niconico-rating')

shut_down_event: Optional[asyncio.Event] = None


async def main():
    try:
        await init()
        # 不等待信号，直接运行GUI
        print("🎯 程序已启动，GUI将在主线程中运行")
    except Exception as e:
        logger.error(f"启动失败: {e}")
        return 1
    return 0


async def init():
    print("🔧 初始化投票系统...")
    init_signal_handlers()
    init_logging()

    print("🔌 初始化blcsdk...")
    await blcsdk.init()
    if not blcsdk.is_sdk_version_compatible():
        raise RuntimeError('SDK version is not compatible')

    print("🚀 初始化listener和GUI...")
    await listener.init()
    print("✅ 初始化完成")


def init_signal_handlers():
    global shut_down_event
    shut_down_event = asyncio.Event()

    signums = (signal.SIGINT, signal.SIGTERM)
    try:
        loop = asyncio.get_running_loop()
        for signum in signums:
            loop.add_signal_handler(signum, start_shut_down)
    except NotImplementedError:
        # 不太安全，但Windows只能用这个
        for signum in signums:
            signal.signal(signum, start_shut_down)


def start_shut_down(*_args):
    shut_down_event.set()


def init_logging():
    # 确保日志目录存在
    os.makedirs(config.LOG_PATH, exist_ok=True)
    
    filename = os.path.join(config.LOG_PATH, 'niconico-rating.log')
    stream_handler = logging.StreamHandler()
    file_handler = logging.handlers.TimedRotatingFileHandler(
        filename, encoding='utf-8', when='midnight', backupCount=7, delay=True
    )
    logging.basicConfig(
        format='{asctime} {levelname} [{name}]: {message}',
        style='{',
        level=logging.INFO,
        handlers=[stream_handler, file_handler],
    )


async def run():
    logger.info('Running niconico rating system')
    print("🔄 投票系统运行中，等待信号...")
    await shut_down_event.wait()
    logger.info('Start to shut down')


async def shut_down():
    print("🛑 正在关闭系统...")
    listener.shut_down()
    await blcsdk.shut_down()


if __name__ == '__main__':
    sys.exit(asyncio.run(main()))
