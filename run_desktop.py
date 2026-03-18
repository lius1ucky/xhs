#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_desktop.py — 在桌面端（Mac / Windows）预览 App UI
方便调试，无需打包 APK

使用方式：
    python run_desktop.py
"""
import os, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 模拟手机窗口尺寸
os.environ.setdefault("KIVY_ORIENTATION", "portrait")

from kivy.config import Config
Config.set("graphics", "width",  "400")
Config.set("graphics", "height", "800")
Config.set("graphics", "resizable", "0")
Config.set("input", "mouse", "mouse,disable_multitouch")

from main import XhsApp
XhsApp().run()
