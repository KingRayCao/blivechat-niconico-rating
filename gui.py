# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import ttk, messagebox
import re
import threading
import time
from typing import Dict, List, Optional
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

class VoteSystemGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("niconico风格弹幕投票系统")
        self.root.geometry("800x600")
        
        # 投票数据 - 默认只匹配数字1-5
        self.vote_levels = {
            1: r"^1$",
            2: r"^2$", 
            3: r"^3$",
            4: r"^4$",
            5: r"^5$"
        }
        
        # 统计状态
        self.is_counting = False
        self.initial_count = 0
        self.vote_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        self.vote_records = dict()
        self.total_votes = 0
        
        # 结果页面设置
        self.result_title = "投票结果"
        self.result_subtitle = "弹幕投票统计"
        
        self.setup_ui()
        
    def setup_ui(self):
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # 1. 投票弹幕设置
        vote_frame = ttk.LabelFrame(main_frame, text="投票弹幕设置", padding="5")
        vote_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # 说明文字
        ttk.Label(vote_frame, text="请输入各等级对应的正则表达式，留空则使用默认值（只匹配数字1-5）", 
                 font=("", 9)).grid(row=0, column=0, columnspan=4, sticky=tk.W, pady=(0, 10))
        
        self.vote_entries = {}
        for i, level in enumerate([1, 2, 3, 4, 5]):
            ttk.Label(vote_frame, text=f"等级 {level}:").grid(row=i+1, column=0, sticky=tk.W, padx=(0, 5))
            entry = ttk.Entry(vote_frame, width=50)
            entry.grid(row=i+1, column=1, sticky=(tk.W, tk.E), padx=(0, 5))
            self.vote_entries[level] = entry
            
            # 测试按钮
            test_btn = ttk.Button(vote_frame, text="测试", 
                                command=lambda l=level: self.test_regex(l))
            test_btn.grid(row=i+1, column=2, padx=(0, 5))
        
        # 设置按钮
        self.setup_btn = ttk.Button(vote_frame, text="设置", command=self.apply_settings)
        self.setup_btn.grid(row=6, column=0, columnspan=4, pady=(10, 0))
        
        vote_frame.columnconfigure(1, weight=1)
        
        # 2. 统计设置
        stats_frame = ttk.LabelFrame(main_frame, text="统计设置", padding="5")
        stats_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(stats_frame, text="初始人数:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.initial_count_entry = ttk.Entry(stats_frame, width=10)
        self.initial_count_entry.insert(0, "0")
        self.initial_count_entry.grid(row=0, column=1, sticky=tk.W, padx=(0, 20))
        
        self.start_btn = ttk.Button(stats_frame, text="开始统计", command=self.start_counting)
        self.start_btn.grid(row=0, column=2, padx=(0, 5))
        
        self.stop_btn = ttk.Button(stats_frame, text="结束统计", command=self.stop_counting, state="disabled")
        self.stop_btn.grid(row=0, column=3)
        
        # 3. 实时统计结果显示
        realtime_frame = ttk.LabelFrame(main_frame, text="实时统计结果", padding="5")
        realtime_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # 创建表格显示投票结果
        columns = ('等级', '票数', '百分比')
        self.tree = ttk.Treeview(realtime_frame, columns=columns, show='headings', height=5)
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100, anchor='center')
        
        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 滚动条
        scrollbar = ttk.Scrollbar(realtime_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        realtime_frame.columnconfigure(0, weight=1)
        realtime_frame.rowconfigure(0, weight=1)
        
        # 总计信息
        self.total_label = ttk.Label(realtime_frame, text="总票数: 0")
        self.total_label.grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        
        # 4. 结果页面设置
        result_frame = ttk.LabelFrame(main_frame, text="结果页面设置", padding="5")
        result_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(result_frame, text="标题:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.title_entry = ttk.Entry(result_frame, width=30)
        self.title_entry.insert(0, self.result_title)
        self.title_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 20))
        
        ttk.Label(result_frame, text="副标题:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        self.subtitle_entry = ttk.Entry(result_frame, width=30)
        self.subtitle_entry.insert(0, self.result_subtitle)
        self.subtitle_entry.grid(row=0, column=3, sticky=(tk.W, tk.E))
        
        result_frame.columnconfigure(1, weight=1)
        result_frame.columnconfigure(3, weight=1)
        
        # 显示结果按钮
        self.show_result_btn = ttk.Button(main_frame, text="显示结果", command=self.show_results)
        self.show_result_btn.grid(row=4, column=0, columnspan=2, pady=(10, 0))
        
        # 配置主框架的网格权重
        main_frame.rowconfigure(2, weight=1)
        
        # 初始化表格数据
        self.update_display()
        
    def apply_settings(self):
        """应用投票设置"""
        try:
            # 更新投票等级设置
            for level, entry in self.vote_entries.items():
                pattern = entry.get().strip()
                if pattern:
                    # 用户输入了自定义正则表达式
                    self.vote_levels[level] = pattern
                else:
                    # 用户留空，使用默认值
                    self.vote_levels[level] = f"^{level}$"
            
            # 更新listener中的正则表达式缓存
            self._update_listener_patterns()
            
            messagebox.showinfo("成功", "投票设置已应用！")
            
        except Exception as e:
            messagebox.showerror("错误", f"应用设置时出错：{str(e)}")
    
    def _update_listener_patterns(self):
        """更新listener中的正则表达式缓存"""
        try:
            import listener
            listener.update_vote_patterns()
        except ImportError:
            # 如果listener模块不可用（比如独立运行模式），忽略错误
            pass
    
    def test_regex(self, level):
        """测试正则表达式"""
        pattern = self.vote_entries[level].get().strip()
        if not pattern:
            pattern = f"^{level}$"  # 使用默认值
            
        try:
            re.compile(pattern)
            messagebox.showinfo("测试结果", f"等级 {level} 的正则表达式有效！\n当前模式: {pattern}")
        except re.error as e:
            messagebox.showerror("错误", f"等级 {level} 的正则表达式无效：{str(e)}")
    
    def start_counting(self):
        """开始统计"""
        try:
            self.initial_count = int(self.initial_count_entry.get())
        except ValueError:
            messagebox.showerror("错误", "请输入有效的初始人数")
            return
            
        self.is_counting = True
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        
        # 重置统计数据
        self.vote_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        self.vote_records = dict()
        self.total_votes = 0
        self.update_display()
        
        # 更新listener中的状态和正则表达式缓存
        self._update_listener_patterns()
        
        messagebox.showinfo("提示", "开始统计投票！")
    
    def stop_counting(self):
        """结束统计"""
        self.is_counting = False
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        
        # 更新listener中的状态
        self._update_listener_patterns()
        
        messagebox.showinfo("提示", "统计已结束！")
    
    def process_vote_by_level(self, uid: str, level: int):
        """根据投票等级直接处理投票（新版本，性能优化）"""
        if not self.is_counting:
            return
            
        # 使用after方法确保在主线程中更新UI
        self.root.after(0, self._update_vote_count, uid, level)
    
    def _update_vote_count(self, uid: str, level: int):
        """在主线程中更新投票计数"""
        if uid not in self.vote_records:
            self.vote_records[uid] = level
            self.vote_counts[level] += 1
            self.total_votes += 1
            self.update_display()
    
    def update_display(self):
        """更新显示"""
        # 清空表格
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # 添加数据
        for level in range(1, 6):
            count = self.vote_counts[level]
            percentage = (count / max(self.total_votes, 1)) * 100
            self.tree.insert('', 'end', values=(f"等级 {level}", count, f"{percentage:.1f}%"))
            
        # 更新总计
        self.total_label.config(text=f"总票数: {self.total_votes}")
    
    def show_results(self):
        """显示结果窗口"""
        if self.total_votes == 0:
            messagebox.showwarning("警告", "暂无投票数据！")
            return
            
        # 创建结果窗口
        result_window = tk.Toplevel(self.root)
        result_window.title("投票结果")
        result_window.geometry("600x500")
        
        # 获取设置
        title = self.title_entry.get()
        subtitle = self.subtitle_entry.get()
        
        # 创建图表
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))
        
        # 柱状图
        levels = list(self.vote_counts.keys())
        counts = list(self.vote_counts.values())
        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7']
        
        bars = ax1.bar(levels, counts, color=colors)
        ax1.set_title('投票分布')
        ax1.set_xlabel('投票等级')
        ax1.set_ylabel('票数')
        
        # 添加数值标签
        for bar, count in zip(bars, counts):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                    f'{count}', ha='center', va='bottom')
        
        # 饼图
        non_zero_counts = [count for count in counts if count > 0]
        non_zero_levels = [f"等级 {level}" for level, count in zip(levels, counts) if count > 0]
        
        if non_zero_counts:
            ax2.pie(non_zero_counts, labels=non_zero_levels, autopct='%1.1f%%', startangle=90)
            ax2.set_title('投票比例')
        
        # 设置总标题
        fig.suptitle(title, fontsize=16, fontweight='bold')
        
        # 添加副标题
        fig.text(0.5, 0.02, subtitle, fontsize=12)
        
        # 嵌入到tkinter窗口
        canvas = FigureCanvasTkAgg(fig, result_window)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # 添加统计信息
        info_frame = ttk.Frame(result_window)
        info_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(info_frame, text=f"总票数: {self.total_votes}").pack(side=tk.LEFT, padx=(0, 20))
        
        max_level = max(self.vote_counts, key=self.vote_counts.get)
        max_count = self.vote_counts[max_level]
        ttk.Label(info_frame, text=f"最高票数: 等级 {max_level} ({max_count} 票)").pack(side=tk.LEFT)
    
    def run(self):
        """运行GUI"""
        self.root.mainloop()

if __name__ == "__main__":
    app = VoteSystemGUI()
    app.run() 