#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
快速检查GUI界面布局的脚本
"""

import wx
import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 模拟必要的模块
class MockListener:
    @staticmethod
    def set_vote_frame(frame):
        pass
    
    @staticmethod
    def update_vote_patterns():
        pass

class MockResultExporter:
    @staticmethod
    def export_result_html(*args, **kwargs):
        print("模拟导出结果")

# 替换导入
sys.modules['listener'] = MockListener()
sys.modules['result_exporter'] = MockResultExporter()

from gui import VoteFrame

class CheckApp(wx.App):
    def OnInit(self):
        frame = VoteFrame(None)
        frame.Show()
        print("GUI界面已启动，请检查界面布局...")
        return True

if __name__ == '__main__':
    app = CheckApp()
    app.MainLoop() 