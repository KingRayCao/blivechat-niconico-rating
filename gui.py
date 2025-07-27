#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import re

import wx
import wx.grid

import listener
import result_exporter

class SilentInfoDialog(wx.Dialog):
    def __init__(self, parent, message, title="提示"):
        super().__init__(parent, title=title, style=wx.DEFAULT_DIALOG_STYLE | wx.STAY_ON_TOP)
        
        self.SetSize((350, 200))
        self.Center()

        # 创建图标和文本
        icon = wx.StaticBitmap(self, bitmap=wx.ArtProvider.GetBitmap(wx.ART_INFORMATION, wx.ART_MESSAGE_BOX))
        text = wx.StaticText(self, label=message)

        # OK按钮
        ok_btn = wx.Button(self, id=wx.ID_OK, label="确定")
        ok_btn.Bind(wx.EVT_BUTTON, self.on_ok)

        # 布局
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add(icon, flag=wx.ALL, border=10)
        hbox.Add(text, flag=wx.ALIGN_CENTER_VERTICAL | wx.ALL, border=10)

        vbox = wx.BoxSizer(wx.VERTICAL)
        vbox.Add(hbox, proportion=1, flag=wx.EXPAND | wx.ALL, border=5)
        vbox.Add(ok_btn, flag=wx.ALIGN_CENTER | wx.BOTTOM, border=10)

        self.SetSizer(vbox)

    def on_ok(self, event):
        self.EndModal(wx.ID_OK)


class VoteFrame(wx.Frame):
    def __init__(self, parent):
        super().__init__(parent, title="niconico风格弹幕投票系统", size=(1000, 700))
        
        self.vote_levels = {1: "^1$", 2: "^2$", 3: "^3$", 4: "^4$", 5: "^5$"}
        self.is_counting = False
        self.vote_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        self.vote_records = {}
        self.total_votes = 0
        
        listener.set_vote_frame(self)
        
        self.setup_ui()
        
        # 定时器用于更新显示
        self.update_timer = wx.Timer(self)
        self.Bind(wx.EVT_TIMER, self.on_update_timer, self.update_timer)
        self.update_timer.Start(100)  # 每100ms更新一次
        
        # 绑定关闭事件
        self.Bind(wx.EVT_CLOSE, self.on_close)
    
    def setup_ui(self):
        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        vote_group = wx.StaticBox(panel, label="投票弹幕设置")
        vote_sizer = wx.StaticBoxSizer(vote_group, wx.VERTICAL)
        
        instruction = wx.StaticText(panel, label="请输入各等级对应的正则表达式，留空则使用默认值（只匹配数字1-5）")
        vote_sizer.Add(instruction, 0, wx.ALL, 5)
        
        self.vote_entries = {}
        vote_grid = wx.FlexGridSizer(5, 3, 5, 5)
        
        for level in range(1, 6):
            label = wx.StaticText(panel, label=f"等级 {level}:")
            vote_grid.Add(label, 0, wx.ALIGN_CENTER_VERTICAL)
            
            entry = wx.TextCtrl(panel, value="", size=(300, -1))
            entry.SetHint(f"默认: ^{level}$")
            self.vote_entries[level] = entry
            vote_grid.Add(entry, 1, wx.EXPAND)
            
            test_btn = wx.Button(panel, label="测试", id=wx.ID_ANY)
            test_btn.Bind(wx.EVT_BUTTON, lambda evt, l=level: self.test_regex(l))
            vote_grid.Add(test_btn, 0)
        
        vote_grid.AddGrowableCol(1, 1)
        vote_sizer.Add(vote_grid, 0, wx.EXPAND | wx.ALL, 5)
        
        self.setup_btn = wx.Button(panel, label="设置")
        self.setup_btn.Bind(wx.EVT_BUTTON, self.apply_settings)
        vote_sizer.Add(self.setup_btn, 0, wx.ALIGN_CENTER | wx.ALL, 5)
        
        main_sizer.Add(vote_sizer, 0, wx.EXPAND | wx.ALL, 5)
        
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
        
        realtime_group = wx.StaticBox(panel, label="实时统计结果")
        realtime_sizer = wx.StaticBoxSizer(realtime_group, wx.VERTICAL)
        
        self.table = wx.grid.Grid(panel)
        self.table.CreateGrid(5, 3)
        self.table.SetColLabelValue(0, "等级")
        self.table.SetColLabelValue(1, "票数")
        self.table.SetColLabelValue(2, "百分比")
        self.table.SetColSize(0, 100)
        self.table.SetColSize(1, 100)
        self.table.SetColSize(2, 100)
        self.table.EnableEditing(False)
        
        realtime_sizer.Add(self.table, 1, wx.EXPAND | wx.ALL, 5)
        
        self.total_label = wx.StaticText(panel, label="总票数: 0")
        font = self.total_label.GetFont()
        font.SetPointSize(12)
        font.SetWeight(wx.FONTWEIGHT_BOLD)
        self.total_label.SetFont(font)
        realtime_sizer.Add(self.total_label, 0, wx.ALL, 5)
        
        main_sizer.Add(realtime_sizer, 1, wx.EXPAND | wx.ALL, 5)
        
        result_group = wx.StaticBox(panel, label="结果页面设置")
        result_sizer = wx.StaticBoxSizer(result_group, wx.VERTICAL)
        
        result_grid = wx.FlexGridSizer(1, 2, 5, 5)
        result_grid.Add(wx.StaticText(panel, label="标题:"), 0, wx.ALIGN_CENTER_VERTICAL)
        self.title_entry = wx.TextCtrl(panel, value="Q. 今日の番組はいかがでしたか？", size=(300, -1))
        result_grid.Add(self.title_entry, 1, wx.EXPAND)
        result_grid.AddGrowableCol(1, 1)
        result_sizer.Add(result_grid, 0, wx.EXPAND | wx.ALL, 5)
        
        self.include_repo_checkbox = wx.CheckBox(panel, label="在结果中包含项目地址")
        self.include_repo_checkbox.SetValue(True)
        result_sizer.Add(self.include_repo_checkbox, 0, wx.LEFT | wx.BOTTOM, 10)
        
        btn_sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.btn_niconico = wx.Button(panel, label="niconico风格统计")
        self.btn_niconico.Bind(wx.EVT_BUTTON, lambda evt: self.show_results(evt, mode="niconico"))
        btn_sizer.Add(self.btn_niconico, 0, wx.RIGHT, 10)
        self.btn_traditional = wx.Button(panel, label="传统风格统计")
        self.btn_traditional.Bind(wx.EVT_BUTTON, lambda evt: self.show_results(evt, mode="traditional"))
        btn_sizer.Add(self.btn_traditional, 0)
        result_sizer.Add(btn_sizer, 0, wx.ALIGN_CENTER | wx.ALL, 5)
        
        main_sizer.Add(result_sizer, 0, wx.EXPAND | wx.ALL, 5)
        
        result_dir = os.path.abspath("result")
        if not os.path.exists(result_dir):
            os.makedirs(result_dir)
        result_path = os.path.join(result_dir, "result.html")
        self.result_html_path = result_path
        self.web_url_text = wx.TextCtrl(panel, value=result_path, style=wx.TE_READONLY)
        main_sizer.Add(self.web_url_text, 0, wx.EXPAND | wx.ALL, 10)
        
        panel.SetSizer(main_sizer)
        self.update_display()
    
    def apply_settings(self, event):
        for level, entry in self.vote_entries.items():
            pattern = entry.GetValue().strip()
            self.vote_levels[level] = pattern if pattern else f"^{level}$"
        listener.update_vote_patterns()
        SilentInfoDialog(self, "投票设置已更新！").ShowModal()
    
    def test_regex(self, level):
        pattern = self.vote_entries[level].GetValue().strip()
        pattern = pattern if pattern else f"^{level}$"
        try:
            re.compile(pattern)
            SilentInfoDialog(self, f"等级 {level} 的正则表达式 '{pattern}' 编译成功！").ShowModal()
        except re.error as e:
            SilentInfoDialog(self, f"等级 {level} 的正则表达式 '{pattern}' 编译失败：{e}").ShowModal()
    
    def start_counting(self, event):
        self.is_counting = True
        self.vote_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        self.vote_records.clear()
        self.total_votes = 0
        try:
            self.total_count = int(self.initial_count_entry.GetValue())
        except ValueError:
            self.total_count = 0
        self.start_btn.Enable(False)
        self.stop_btn.Enable(True)
        self.btn_niconico.Enable(False)
        self.btn_traditional.Enable(False)
        listener.update_vote_patterns()
        
        
        # wx.MessageBox("开始统计投票！", "提示", wx.OK | wx.ICON_INFORMATION)
    
    
        # wx.MessageBox("开始统计投票！", "提示", wx.OK | wx.ICON_INFORMATION)
    
    def stop_counting(self, event):
        self.is_counting = False
        self.total_count = max(self.total_count, self.total_votes)
        self.start_btn.Enable(True)
        self.stop_btn.Enable(False)
        self.btn_niconico.Enable(True)
        self.btn_traditional.Enable(True)
        listener.update_vote_patterns()
        
        
        # wx.MessageBox("统计已结束！", "提示", wx.OK | wx.ICON_INFORMATION)
    
    
        # wx.MessageBox("统计已结束！", "提示", wx.OK | wx.ICON_INFORMATION)
    
    def process_vote_by_level(self, uid: str, level: int):
        if not self.is_counting:
            return
        if uid not in self.vote_records:
            self.vote_records[uid] = level
            self.vote_counts[level] += 1
            self.total_votes += 1
    
    def on_update_timer(self, event):
        self.update_display()
    
    def update_display(self):
        for level in range(1, 6):
            count = self.vote_counts[level]
            percentage = (count / max(self.total_votes, 1)) * 100
            self.table.SetCellValue(level-1, 0, f"等级 {level}")
            self.table.SetCellValue(level-1, 1, str(count))
            self.table.SetCellValue(level-1, 2, f"{percentage:.1f}%")
        self.total_label.SetLabel(f"总票数: {self.total_votes}")
    
    def show_results(self, event, mode="niconico"):
        vote_counts = [self.vote_counts[i] for i in range(1,6)]
        labels = ["とても良かった", "まぁまぁ良かった", "ふつうだった", "あまり良くなかった", "良くなかった"]
        include_repo = self.include_repo_checkbox.GetValue()
        result_exporter.export_result_html(
            self.title_entry.GetValue(), vote_counts, self.total_count, labels,
            filename=self.result_html_path, mode=mode, include_repo=include_repo
        )
        SilentInfoDialog(self, f"HTML结果已导出\n请在OBS中使用浏览器源查看下方URL\n浏览器源推荐尺寸:900*600\n请注意，浏览器源的尺寸会影响投票结果的显示效果").ShowModal()
    
    def on_close(self, event):
        SilentInfoDialog(self, "为防止误操作，此界面无法被关闭！\n如需关闭，请直接关闭blivechat主程序！").ShowModal()
