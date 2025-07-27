# -*- coding: utf-8 -*-
import __main__
import datetime
import logging
import os
import sys
import threading
import re
from typing import *

import blcsdk
import blcsdk.models as sdk_models
import config
import gui

logger = logging.getLogger('niconico-rating.' + __name__)

_msg_handler: Optional['VoteHandler'] = None
_gui_app: Optional[gui.VoteSystemGUI] = None


async def init():
    global _msg_handler, _gui_app
    
    print("🎨 创建GUI...")
    # 创建GUI但不启动
    _gui_app = gui.VoteSystemGUI()
    print("✅ GUI创建完成")
    
    print("📡 设置消息处理器...")
    _msg_handler = VoteHandler()
    blcsdk.set_msg_handler(_msg_handler)
    
    # 创建已有的房间。这一步失败了也没关系，只是有消息时才会创建文件
    try:
        blc_rooms = await blcsdk.get_rooms()
        for blc_room in blc_rooms:
            if blc_room.room_id is not None:
                logger.info(f'发现已有房间: {blc_room.room_id}')
    except blcsdk.SdkError:
        pass
    
    logger.info('niconico风格投票系统已启动')
    print("🎉 投票系统启动完成！")
    
    # 启动GUI（在主线程中）
    print("🚀 启动GUI...")
    _gui_app.run()


def shut_down():
    blcsdk.set_msg_handler(None)
    if _gui_app:
        _gui_app.root.quit()


class VoteHandler(blcsdk.BaseHandler):
    def __init__(self):
        super().__init__()
        # 缓存编译后的正则表达式，提高性能
        self._compiled_patterns = {}
        self._is_counting = False
        self._update_patterns()
    
    def _update_patterns(self):
        """更新编译后的正则表达式"""
        if not _gui_app:
            return
            
        self._compiled_patterns.clear()
        self._is_counting = _gui_app.is_counting
        
        if not self._is_counting:
            return
            
        # 获取GUI中的投票等级设置并编译
        for level, pattern in _gui_app.vote_levels.items():
            try:
                self._compiled_patterns[level] = re.compile(pattern)
            except re.error as e:
                logger.warning(f'等级 {level} 的正则表达式编译失败: {pattern}, 错误: {e}')
    
    def _should_process_vote(self, content: str) -> bool:
        """判断是否需要处理投票消息"""
        if not self._is_counting:
            return False
            
        content = content.strip()
        if not content:
            return False
            
        # 检查是否匹配任何投票等级
        for level, pattern in self._compiled_patterns.items():
            if pattern.match(content):
                return True
                
        return False
    
    def _get_vote_level(self, content: str) -> Optional[int]:
        """获取投票等级，如果不匹配则返回None"""
        content = content.strip()
        for level, pattern in self._compiled_patterns.items():
            if pattern.match(content):
                return level
        return None

    def on_client_stopped(self, client: blcsdk.BlcPluginClient, exception: Optional[Exception]):
        logger.info('blivechat disconnected')
        __main__.start_shut_down()

    def _on_open_plugin_admin_ui(
        self, client: blcsdk.BlcPluginClient, message: sdk_models.OpenPluginAdminUiMsg, extra: sdk_models.ExtraData
    ):
        # 打开GUI窗口
        if _gui_app:
            _gui_app.root.lift()
            _gui_app.root.focus_force()

    def _on_add_room(
        self, client: blcsdk.BlcPluginClient, message: sdk_models.AddRoomMsg, extra: sdk_models.ExtraData
    ):
        """添加房间"""
        if extra.is_from_plugin:
            return
        logger.info(f'添加房间: {extra.room_key}')

    def _on_room_init(
        self, client: blcsdk.BlcPluginClient, message: sdk_models.RoomInitMsg, extra: sdk_models.ExtraData
    ):
        if extra.is_from_plugin:
            return
        if message.is_success:
            logger.info(f'房间 {extra.room_id} 初始化成功')

    def _on_del_room(self, client: blcsdk.BlcPluginClient, message: sdk_models.DelRoomMsg, extra: sdk_models.ExtraData):
        if extra.is_from_plugin:
            return
        if extra.room_id is not None:
            logger.info(f'房间 {extra.room_id} 已删除')

    def _on_add_text(self, client: blcsdk.BlcPluginClient, message: sdk_models.AddTextMsg, extra: sdk_models.ExtraData):
        logger.info(f'收到弹幕: {message.author_name}: {message.content}')

        if extra.is_from_plugin:
            return
        
        # 预过滤：只处理可能匹配的弹幕
        if self._should_process_vote(message.content):
            # 获取投票等级
            vote_level = self._get_vote_level(message.content)
            if vote_level and _gui_app:
                # 直接传递投票等级给GUI，避免重复匹配
                _gui_app.process_vote_by_level(message.uid, vote_level)
                # logger.debug(f'投票弹幕: {message.author_name}: {message.content} -> 等级 {vote_level}')
        # else:
            # 记录非投票弹幕（可选，用于调试）
            # logger.debug(f'收到弹幕: {message.author_name}: {message.content}')

    def _on_add_gift(self, client: blcsdk.BlcPluginClient, message: sdk_models.AddGiftMsg, extra: sdk_models.ExtraData):
        # 礼物消息不参与投票
        pass

    def _on_add_member(
        self, client: blcsdk.BlcPluginClient, message: sdk_models.AddMemberMsg, extra: sdk_models.ExtraData
    ):
        # 舰队消息不参与投票
        pass

    def _on_add_super_chat(
        self, client: blcsdk.BlcPluginClient, message: sdk_models.AddSuperChatMsg, extra: sdk_models.ExtraData
    ):
        # 醒目留言不参与投票
        pass


# 提供给GUI调用的函数，用于更新listener中的正则表达式缓存
def update_vote_patterns():
    """更新投票正则表达式缓存"""
    if _msg_handler:
        _msg_handler._update_patterns()
        logger.debug('投票正则表达式缓存已更新')
