#!/usr/bin/env python
# -*- coding: utf-8 -*-
import __main__
import logging
import re
from typing import Optional, TYPE_CHECKING

import wx

import blcsdk
import blcsdk.api as sdk_api
import blcsdk.models as sdk_models
import config

if TYPE_CHECKING:
    from gui import VoteFrame

logger = logging.getLogger('niconico-rating.' + __name__)

_msg_handler: Optional['VoteHandler'] = None
_vote_frame: Optional['VoteFrame'] = None


async def init():
    global _msg_handler
    
    print("📡 设置消息处理器...")
    _msg_handler = VoteHandler()
    blcsdk.set_msg_handler(_msg_handler)
    print("✅ 消息处理器设置完成")
    
    # 房间管理（仅日志记录，不创建文件）
    try:
        blc_rooms = await sdk_api.get_rooms()
        for blc_room in blc_rooms:
            if blc_room.room_id is not None:
                logger.info(f'发现已有房间: {blc_room.room_id}')
    except sdk_api.SdkError:
        pass
    
    logger.info('niconico风格投票系统已启动')
    print("🎉 投票系统启动完成！")


def shut_down():
    blcsdk.set_msg_handler(None)


def set_vote_frame(frame):
    """设置投票窗口引用"""
    global _vote_frame
    _vote_frame = frame


class VoteHandler(blcsdk.BaseHandler):
    def __init__(self):
        super().__init__()
        # 缓存编译后的正则表达式，提高性能
        self._compiled_patterns = {}
        self._is_counting = False
        self._update_patterns()
        logger.info("VoteHandler初始化完成")
    
    def _update_patterns(self):
        """更新编译后的正则表达式"""
        if not _vote_frame:
            logger.warning("GUI应用未初始化，无法更新正则表达式")
            return
            
        self._compiled_patterns.clear()
        self._is_counting = _vote_frame.is_counting
        
        if not self._is_counting:
            logger.info("当前未在统计状态，正则表达式已清空")
            return
        
        # 获取GUI中的投票等级设置并编译
        for level, pattern in _vote_frame.vote_levels.items():
            try:
                self._compiled_patterns[level] = re.compile(pattern)
                logger.debug(f"等级 {level} 正则表达式编译成功: {pattern}")
            except re.error as e:
                logger.warning(f'等级 {level} 的正则表达式编译失败: {pattern}, 错误: {e}')
        logger.info(f"正则表达式更新完成，共 {len(self._compiled_patterns)} 个模式")
    
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
        wx.CallAfter(__main__.start_shut_down)

    def _on_open_plugin_admin_ui(
        self, client: blcsdk.BlcPluginClient, message: sdk_models.OpenPluginAdminUiMsg, extra: sdk_models.ExtraData
    ):
        # 打开GUI窗口
        if _vote_frame:
            wx.CallAfter(_vote_frame.Raise)
            wx.CallAfter(_vote_frame.SetFocus)

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
        if extra.is_from_plugin:
            return
        
        # 记录所有非插件弹幕
        logger.info(f'收到弹幕: {message.author_name}: {message.content}')

        # 预过滤：只处理可能匹配的弹幕
        if self._should_process_vote(message.content):
            # 获取投票等级
            vote_level = self._get_vote_level(message.content)
            if vote_level and _vote_frame:
                # 使用wx.CallAfter确保在主线程中更新GUI
                wx.CallAfter(_vote_frame.process_vote_by_level, message.uid, vote_level)
                logger.debug(f'投票弹幕: {message.author_name}: {message.content} -> 等级 {vote_level}')
            else:
                logger.warning(f'投票弹幕处理失败: vote_level={vote_level}, _vote_frame={_vote_frame is not None}')
        else:
            logger.debug(f'弹幕不匹配投票规则: {message.content}')

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
