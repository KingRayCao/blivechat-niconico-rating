# -*- coding: utf-8 -*-
import os

BASE_PATH = os.path.dirname(os.path.realpath(__file__))
LOG_PATH = os.path.join(BASE_PATH, 'log')

# 投票等级设置 - 默认只匹配数字1-5
VOTE_LEVELS = {
    1: r"^1$",
    2: r"^2$", 
    3: r"^3$",
    4: r"^4$",
    5: r"^5$"
}

# 默认结果页面设置
DEFAULT_RESULT_TITLE = "投票结果"
DEFAULT_RESULT_SUBTITLE = "弹幕投票统计"
