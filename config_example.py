# -*- coding: utf-8 -*-
"""
配置文件示例
可以复制此文件为config.py并修改设置
"""

import os

BASE_PATH = os.path.dirname(os.path.realpath(__file__))
LOG_PATH = os.path.join(BASE_PATH, 'log')

# 投票等级设置 - 可以根据需要修改
VOTE_LEVELS = {
    # 示例1: 简单数字投票（默认）
    1: r"^1$",
    2: r"^2$", 
    3: r"^3$",
    4: r"^4$",
    5: r"^5$"
    
    # 示例2: 多语言投票 (取消注释使用)
    # 1: r"^[1一壹Ⅰ]$",
    # 2: r"^[2二贰Ⅱ]$", 
    # 3: r"^[3三叁Ⅲ]$",
    # 4: r"^[4四肆Ⅳ]$",
    # 5: r"^[5五伍Ⅴ]$"
    
    # 示例3: 关键词投票 (取消注释使用)
    # 1: r"^(好|棒|赞|优秀|完美)$",
    # 2: r"^(不错|还行|可以|一般)$", 
    # 3: r"^(普通|一般|还行)$",
    # 4: r"^(不好|差|糟糕|不行)$",
    # 5: r"^(很差|极差|垃圾|最差)$"
    
    # 示例4: 英文关键词投票 (取消注释使用)
    # 1: r"^(good|great|excellent|perfect|awesome)$",
    # 2: r"^(okay|fine|alright|decent)$", 
    # 3: r"^(average|normal|mediocre)$",
    # 4: r"^(bad|poor|terrible|awful)$",
    # 5: r"^(worst|horrible|terrible|awful)$"
    
    # 示例5: 范围投票 (取消注释使用)
    # 1: r"^[1-2]$",
    # 2: r"^[3-4]$", 
    # 3: r"^[5-6]$",
    # 4: r"^[7-8]$",
    # 5: r"^[9-10]$"
    
    # 示例6: 表情符号投票 (取消注释使用)
    # 1: r"^[😀😃😄😁😆😅😂🤣😊😇]$",
    # 2: r"^[😉😌😍🥰😘😗😙😚😋😛]$", 
    # 3: r"^[😐😑😶😏😒🙄😬🤥😪😴]$",
    # 4: r"^[😷🤒🤕🤢🤧😈👿👹👺🤡]$",
    # 5: r"^[💀☠️👻👽👾🤖😺😸😹😻]$"
}

# 结果页面设置
DEFAULT_RESULT_TITLE = "投票结果"
DEFAULT_RESULT_SUBTITLE = "弹幕投票统计"

# 高级设置
# 是否启用调试模式
DEBUG_MODE = False

# 日志级别
LOG_LEVEL = "INFO"  # DEBUG, INFO, WARNING, ERROR

# GUI窗口设置
GUI_WIDTH = 800
GUI_HEIGHT = 600

# 投票统计设置
# 是否允许重复投票 (同一用户)
ALLOW_DUPLICATE_VOTES = True

# 投票时间限制 (秒，0表示无限制)
VOTE_TIME_LIMIT = 0 