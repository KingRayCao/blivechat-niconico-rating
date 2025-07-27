#!/usr/bin/env python
# -*- coding: utf-8 -*-
import asyncio
import concurrent.futures
import logging
import logging.handlers
import os
import signal
import sys
import threading
from typing import *

import wx

import blcsdk
import listener
from gui import VoteFrame

logger = logging.getLogger('niconico-rating')

app: Optional['VoteApp'] = None


def main():
    init_signal_handlers()
    init_logging()
    
    global app
    app = VoteApp()
    
    logger.info('Running event loop')
    app.MainLoop()


def init_signal_handlers():
    def signal_handler(*_args):
        wx.CallAfter(start_shut_down)

    for signum in (signal.SIGINT, signal.SIGTERM):
        signal.signal(signum, signal_handler)


def start_shut_down():
    if app is not None and app.IsMainLoopRunning():
        app.ExitMainLoop()
    else:
        wx.Exit()


def init_logging():
    # 确保日志目录存在
    os.makedirs('log', exist_ok=True)
    
    filename = os.path.join('log', 'niconico-rating.log')
    # 启动时清空log文件
    with open(filename, 'w', encoding='utf-8'):
        pass
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


class VoteApp(wx.App):
    def __init__(self, *args, **kwargs):
        self._network_worker = NetworkWorker()
        self._dummy_timer: Optional[wx.Timer] = None
        self._vote_frame: Optional[VoteFrame] = None
        
        super().__init__(*args, clearSigInt=False, **kwargs)
        self.SetExitOnFrameDelete(False)

    def OnInit(self):
        # 这个定时器只是为了及时响应信号，因为只有处理UI事件时才会唤醒主线程
        self._dummy_timer = wx.Timer(self)
        self._dummy_timer.Start(1000)
        self.Bind(wx.EVT_TIMER, lambda _event: None, self._dummy_timer)

        # 创建投票窗口
        self._vote_frame = VoteFrame(None)
        self._vote_frame.Show()

        # 初始化网络工作线程
        self._network_worker.init()
        return True

    def OnExit(self):
        logger.info('Start to shut down')
        
        self._network_worker.start_shut_down()
        self._network_worker.join(10)
        
        return super().OnExit()


class NetworkWorker:
    def __init__(self):
        self._worker_thread = threading.Thread(
            target=asyncio.run, args=(self._worker_thread_func(),), daemon=True
        )
        self._thread_init_future = concurrent.futures.Future()
        
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._shut_down_event: Optional[asyncio.Event] = None

    def init(self):
        self._worker_thread.start()
        self._thread_init_future.result(10)

    def start_shut_down(self):
        if self._shut_down_event is not None:
            self._loop.call_soon_threadsafe(self._shut_down_event.set)

    def join(self, timeout=None):
        self._worker_thread.join(timeout)
        return not self._worker_thread.is_alive()

    async def _worker_thread_func(self):
        self._loop = asyncio.get_running_loop()
        try:
            try:
                await self._init_in_worker_thread()
                self._thread_init_future.set_result(None)
            except BaseException as e:
                self._thread_init_future.set_exception(e)
                return

            await self._run()
        finally:
            await self._shut_down()

    async def _init_in_worker_thread(self):
        await blcsdk.init()
        if not blcsdk.is_sdk_version_compatible():
            raise RuntimeError('SDK version is not compatible')

        await listener.init()
        
        self._shut_down_event = asyncio.Event()

    async def _run(self):
        logger.info('Running network thread event loop')
        await self._shut_down_event.wait()
        logger.info('Network thread start to shut down')

    @staticmethod
    async def _shut_down():
        listener.shut_down()
        await blcsdk.shut_down()


if __name__ == '__main__':
    main()
