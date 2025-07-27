#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re
import threading
import time
from typing import Dict, Optional

import wx
import wx.grid
import matplotlib.pyplot as plt
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np

import config
import listener

# 设置matplotlib字体以支持中文
import matplotlib
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False


class VoteFrame(wx.Frame):
    def __init__(self, parent):
        super().__init__(parent, title="niconico风格弹幕投票系统", size=(1000, 700))
        
        # 投票数据
        self.vote_levels = {1: "^1$", 2: "^2$", 3: "^3$", 4: "^4$", 5: "^5$"}
        self.is_counting = False
        self.vote_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        self.vote_records = {}
        self.total_votes = 0
        
        # 设置窗口引用到listener
        listener.set_vote_frame(self)
        
        # 设置UI
        self.setup_ui()
        
        # 定时器用于更新显示
        self.update_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_update_timer, self.update_timer)
        self.update_timer.Start(100)  # 每100ms更新一次
        
        # 绑定关闭事件
        self.Bind(wx.EVT_CLOSE, self.on_close)
    
    def setup_ui(self):
        """设置用户界面"""
        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 1. 投票弹幕设置
        vote_group = wx.StaticBox(panel, label="投票弹幕设置")
        vote_sizer = wx.StaticBoxSizer(vote_group, wx.VERTICAL)
        
        # 说明文字
        instruction = wx.StaticText(panel, label="请输入各等级对应的正则表达式，留空则使用默认值（只匹配数字1-5）")
        vote_sizer.Add(instruction, 0, wx.ALL, 5)
        
        # 投票等级输入框
        self.vote_entries = {}
        vote_grid = wx.FlexGridSizer(5, 3, 5, 5)
        
        for level in range(1, 6):
            # 等级标签
            label = wx.StaticText(panel, label=f"等级 {level}:")
            vote_grid.Add(label, 0, wx.ALIGN_CENTER_VERTICAL)
            
            # 输入框
            entry = wx.TextCtrl(panel, value="", size=(300, -1))
            entry.SetHint(f"默认: ^{level}$")
            self.vote_entries[level] = entry
            vote_grid.Add(entry, 1, wx.EXPAND)
            
            # 测试按钮
            test_btn = wx.Button(panel, label="测试", id=wx.ID_ANY)
            test_btn.Bind(wx.EVT_BUTTON, lambda evt, l=level: self.test_regex(l))
            vote_grid.Add(test_btn, 0)
        
        vote_grid.AddGrowableCol(1, 1)
        vote_sizer.Add(vote_grid, 0, wx.EXPAND | wx.ALL, 5)
        
        # 设置按钮
        self.setup_btn = wx.Button(panel, label="设置")
        self.setup_btn.Bind(wx.EVT_BUTTON, self.apply_settings)
        vote_sizer.Add(self.setup_btn, 0, wx.ALIGN_CENTER | wx.ALL, 5)
        
        main_sizer.Add(vote_sizer, 0, wx.EXPAND | wx.ALL, 5)
        
        # 2. 统计设置
        stats_group = wx.StaticBox(panel, label="统计设置")
        stats_sizer = wx.StaticBoxSizer(stats_group, wx.HORIZONTAL)
        
        stats_sizer.Add(wx.StaticText(panel, label="初始人数:"), 0, wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 5)
        
        self.initial_count_entry = wx.TextCtrl(panel, value="0", size=(100, -1))
        stats_sizer.Add(self.initial_count_entry, 0, wx.RIGHT, 20)
        
        self.start_btn = wx.Button(panel, label="开始统计")
        self.start_btn.Bind(wx.EVT_BUTTON, self.start_counting)
        stats_sizer.Add(self.start_btn, 0, wx.RIGHT, 5)
        
        self.stop_btn = wx.Button(panel, label="结束统计")
        self.stop_btn.Bind(wx.EVT_BUTTON, self.stop_counting)
        self.stop_btn.Enable(False)
        stats_sizer.Add(self.stop_btn, 0)
        
        stats_sizer.AddStretchSpacer()
        main_sizer.Add(stats_sizer, 0, wx.EXPAND | wx.ALL, 5)
        
        # 3. 实时统计结果显示
        realtime_group = wx.StaticBox(panel, label="实时统计结果")
        realtime_sizer = wx.StaticBoxSizer(realtime_group, wx.VERTICAL)
        
        # 创建表格
        self.table = wx.grid.Grid(panel)
        self.table.CreateGrid(5, 3)
        self.table.SetColLabelValue(0, "等级")
        self.table.SetColLabelValue(1, "票数")
        self.table.SetColLabelValue(2, "百分比")
        
        # 设置表格属性
        self.table.SetColSize(0, 100)
        self.table.SetColSize(1, 100)
        self.table.SetColSize(2, 100)
        self.table.EnableEditing(False)
        
        realtime_sizer.Add(self.table, 1, wx.EXPAND | wx.ALL, 5)
        
        # 总票数显示
        self.total_label = wx.StaticText(panel, label="总票数: 0")
        font = self.total_label.GetFont()
        font.SetPointSize(12)
        font.SetWeight(wx.FONTWEIGHT_BOLD)
        self.total_label.SetFont(font)
        realtime_sizer.Add(self.total_label, 0, wx.ALL, 5)
        
        main_sizer.Add(realtime_sizer, 1, wx.EXPAND | wx.ALL, 5)
        
        # 4. 结果页面设置
        result_group = wx.StaticBox(panel, label="结果页面设置")
        result_sizer = wx.StaticBoxSizer(result_group, wx.VERTICAL)
        
        result_grid = wx.FlexGridSizer(1, 2, 5, 5)
        
        result_grid.Add(wx.StaticText(panel, label="标题:"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.title_entry = wx.TextCtrl(panel, value="投票结果", size=(300, -1))
        result_grid.Add(self.title_entry, 1, wx.EXPAND)
        
        result_grid.AddGrowableCol(1, 1)
        result_sizer.Add(result_grid, 0, wx.EXPAND | wx.ALL, 5)
        
        # 两种统计方式按钮
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_niconico = wx.Button(panel, label="niconico风格统计")
        self.btn_niconico.Bind(wx.EVT_BUTTON, lambda evt: self.show_results(evt, mode="niconico"))
        btn_sizer.Add(self.btn_niconico, 0, wx.RIGHT, 10)
        self.btn_traditional = wx.Button(panel, label="传统风格统计")
        self.btn_traditional.Bind(wx.EVT_BUTTON, lambda evt: self.show_results(evt, mode="traditional"))
        btn_sizer.Add(self.btn_traditional, 0)
        result_sizer.Add(btn_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 5)
        
        main_sizer.Add(result_sizer, 0, wx.EXPAND | wx.ALL, 5)
        
        panel.SetSizer(main_sizer)
        
        # 初始化表格
        self.update_display()
    
    def apply_settings(self, event):
        """应用投票设置"""
        for level, entry in self.vote_entries.items():
            pattern = entry.GetValue().strip()
            if pattern:
                # 用户输入了自定义正则表达式
                self.vote_levels[level] = pattern
            else:
                # 用户留空，使用默认值
                self.vote_levels[level] = f"^{level}$"
        
        # 更新listener中的正则表达式缓存
        listener.update_vote_patterns()
        
        wx.MessageBox("投票设置已更新！", "提示", wx.OK | wx.ICON_INFORMATION)
    
    def test_regex(self, level):
        """测试正则表达式"""
        pattern = self.vote_entries[level].GetValue().strip()
        if not pattern:
            pattern = f"^{level}$"  # 使用默认值
        
        try:
            re.compile(pattern)
            wx.MessageBox(f"等级 {level} 的正则表达式 '{pattern}' 编译成功！", 
                         "测试结果", wx.OK | wx.ICON_INFORMATION)
        except re.error as e:
            wx.MessageBox(f"等级 {level} 的正则表达式 '{pattern}' 编译失败：{e}", 
                         "测试结果", wx.OK | wx.ICON_WARNING)
    
    def start_counting(self, event):
        """开始统计"""
        self.is_counting = True
        
        # 重置投票数据
        self.vote_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        self.vote_records.clear()
        self.total_votes = 0
        
        # 设置初始人数
        try:
            total_count = int(self.initial_count_entry.GetValue())
            self.total_count = total_count
        except ValueError:
            self.total_count = 0

        self.start_btn.Enable(False)
        self.stop_btn.Enable(True)
        
        # 禁用可视化按钮
        self.btn_niconico.Enable(False)
        self.btn_traditional.Enable(False)
        
        # 更新listener中的状态和正则表达式缓存
        listener.update_vote_patterns()
        
        # wx.MessageBox("开始统计投票！", "提示", wx.OK | wx.ICON_INFORMATION)
    
    def stop_counting(self, event):
        """结束统计"""
        self.is_counting = False
        self.total_count = max(self.total_count, self.total_votes)
        
        self.start_btn.Enable(True)
        self.stop_btn.Enable(False)
        
        # 启用可视化按钮
        self.btn_niconico.Enable(True)
        self.btn_traditional.Enable(True)
        
        # 更新listener中的状态
        listener.update_vote_patterns()
        
        # wx.MessageBox("统计已结束！", "提示", wx.OK | wx.ICON_INFORMATION)
    
    def process_vote_by_level(self, uid: str, level: int):
        """根据投票等级直接处理投票（供外部调用）"""
        if not self.is_counting:
            return
        
        # 检查是否已经投票
        # if uid not in self.vote_records:
        #     self.vote_records[uid] = level
        #     self.vote_counts[level] += 1
        #     self.total_votes += 1
        # 测试用
        self.vote_counts[level] += 1
        self.total_votes += 1
    
    def on_update_timer(self, event):
        """定时器事件，更新显示"""
        self.update_display()
    
    def update_display(self):
        """更新显示"""
        for level in range(1, 6):
            count = self.vote_counts[level]
            percentage = (count / max(self.total_votes, 1)) * 100
            
            self.table.SetCellValue(level-1, 0, f"等级 {level}")
            self.table.SetCellValue(level-1, 1, str(count))
            self.table.SetCellValue(level-1, 2, f"{percentage:.1f}%")
        
        self.total_label.SetLabel(f"总票数: {self.total_votes}")
    
    def show_results(self, event, mode="niconico"):
        """显示结果窗口"""
        if self.total_votes == 0:
            wx.MessageBox("暂无投票数据！", "警告", wx.OK | wx.ICON_WARNING)
            return
        
        # 创建结果窗口
        result_window = ResultWindow(self, "投票结果", (800, 600), mode=mode)
        result_window.Show()
    
    def on_close(self, event):
        """窗口关闭事件"""
        print("🛑 GUI窗口正在关闭...")
        self.update_timer.Stop()
        event.Skip()


class ResultWindow(wx.Frame):
    LABELS = [
        "とても良かった",
        "まぁまぁ良かった",
        "ふつうだった",
        "あまり良くなかった",
        "良くなかった"
    ]
    COLORS = [
        "#4FC3F7",  # 蓝
        "#4FC3F7",  # 蓝
        "#4FC3F7",  # 蓝
        "#4FC3F7",  # 蓝
        "#4FC3F7",  # 蓝
    ]
    CARD_SIZE = (220, 120)

    def __init__(self, parent, title, size, mode="niconico"):
        super().__init__(parent, title=title, size=size)
        self.mode = mode
        self.vote_counts = parent.vote_counts.copy()
        self.total_count = parent.total_count
        self.setup_ui()

    def setup_ui(self):
        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        # 计算百分比
        if self.total_count == 0:
            percents = [0] * 5
        else:
            if self.mode == "niconico":
                nico_counts = self.vote_counts.copy()
                nico_counts[1] = max(self.total_count - sum(nico_counts[l] for l in range(2, 6)), 0)
                counts = [nico_counts[l] for l in range(1, 6)]
            else:
                counts = [self.vote_counts[l] for l in range(1, 6)]
            percents = [count / max(self.total_count, 1) * 100 for count in counts]
        # 2+3布局，4/5居中
        grid = wx.FlexGridSizer(2, 3, 15, 15)
        # 上排1,2,3
        for i in range(3):
            card = self.create_card(panel, i + 1, self.LABELS[i], percents[i], self.COLORS[i])
            grid.Add(card, 1, wx.EXPAND)
        # 下排：空，4，5
        grid.Add((0, 0))  # 左空
        card4 = self.create_card(panel, 4, self.LABELS[3], percents[3], self.COLORS[3])
        grid.Add(card4, 1, wx.EXPAND)
        card5 = self.create_card(panel, 5, self.LABELS[4], percents[4], self.COLORS[4])
        grid.Add(card5, 1, wx.EXPAND)
        main_sizer.Add(grid, 1, wx.ALL | wx.EXPAND, 30)
        panel.SetSizer(main_sizer)
        self.Centre()

    def create_card(self, parent_panel, idx, label, percent, color):
        panel = wx.Panel(parent_panel, size=(220, 120))
        panel.SetBackgroundColour(color)
        panel.SetWindowStyle(wx.BORDER_SIMPLE)
        font_percent = wx.Font(24, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        font_label = wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        font_idx = wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
        sizer = wx.BoxSizer(wx.VERTICAL)
        idx_text = wx.StaticText(panel, label=str(idx))
        idx_text.SetFont(font_idx)
        idx_text.SetForegroundColour("#333333")
        sizer.Add(idx_text, 0, wx.TOP | wx.LEFT, 8)
        percent_text = wx.StaticText(panel, label=f"{percent:.1f}%")
        percent_text.SetFont(font_percent)
        percent_text.SetForegroundColour("#222222")
        sizer.Add(percent_text, 0, wx.ALIGN_CENTER | wx.TOP, 5)
        label_text = wx.StaticText(panel, label=label)
        label_text.SetFont(font_label)
        label_text.SetForegroundColour("#222222")
        sizer.Add(label_text, 0, wx.ALIGN_CENTER | wx.TOP | wx.BOTTOM, 5)
        panel.SetSizer(sizer)
        return panel 