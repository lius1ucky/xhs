#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
main.py — 小红书运营工具箱 Android App 入口
基于 Kivy 2.2+，支持 Android / Mac / Windows
"""

import os
import sys
import platform
from datetime import datetime

# 将项目根目录加入 path
ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.modalview import ModalView
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import StringProperty, NumericProperty, ListProperty
from kivy.clock import Clock, mainthread
from kivy.core.text import LabelBase
from kivy.metrics import dp, sp
from kivy.utils import platform as kivy_platform

from core import config, tasks

# ─────────────────────────────────────────────
# 字体路径检测
# ─────────────────────────────────────────────
def find_font():
    """跨平台查找中文字体，返回路径或 None"""
    system = platform.system()
    candidates = []

    if system == "Darwin":
        candidates = [
            "/System/Library/Fonts/PingFang.ttc",
            "/System/Library/Fonts/STHeiti Light.ttc",
        ]
    elif system == "Windows":
        candidates = [
            "C:/Windows/Fonts/msyh.ttc",
            "C:/Windows/Fonts/simhei.ttf",
        ]
    # Android: 字体放在 assets/fonts 目录
    candidates += [
        os.path.join(ROOT, "assets", "fonts", "NotoSansCJK-Regular.ttc"),
        os.path.join(ROOT, "assets", "fonts", "wqy-microhei.ttc"),
        os.path.join(ROOT, "assets", "fonts", "font.ttf"),
    ]
    # Linux
    candidates += [
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    ]

    for path in candidates:
        if os.path.exists(path):
            return path
    return None


# ─────────────────────────────────────────────
# 评论弹窗
# ─────────────────────────────────────────────
class CommentDialog(ModalView):
    def __init__(self, on_confirm_cb, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (0.9, None)
        self.height = dp(320)
        self.background_color = (0, 0, 0, 0.7)
        self._cb = on_confirm_cb

    def on_confirm(self):
        feed_id = self.ids.feed_id_input.text.strip()
        xsec    = self.ids.xsec_input.text.strip()
        if feed_id and xsec:
            self.dismiss()
            self._cb(feed_id, xsec)
        else:
            self.ids.feed_id_input.hint_text = "⚠️ 不能为空"
            self.ids.xsec_input.hint_text    = "⚠️ 不能为空"


# ─────────────────────────────────────────────
# 主功能界面
# ─────────────────────────────────────────────
class MainScreen(Screen):
    log_text    = StringProperty("欢迎使用小红书运营工具箱 👋\n等待指令...\n")
    status_text = StringProperty("就绪")

    def _append_log(self, msg):
        ts = datetime.now().strftime("%H:%M:%S")
        self.log_text += f"[{ts}] {msg}\n"
        # 自动滚动到底部
        Clock.schedule_once(lambda dt: self._scroll_bottom(), 0.1)

    def _scroll_bottom(self):
        scroll = self.ids.get("log_scroll")
        if scroll:
            scroll.scroll_y = 0

    @mainthread
    def log(self, msg):
        self._append_log(msg)

    def clear_log(self):
        self.log_text = ""

    def set_status(self, text):
        self.status_text = text

    # ── 搜索热点 ──
    def on_search(self):
        cfg = config.load()
        keywords = cfg.get("hotspot_keywords", ["科技热点"])
        keyword = keywords[0] if keywords else "科技热点"
        self.log(f"开始搜索热点: {keyword}")
        self.set_status("搜索中...")
        tasks.search_hotspot_async(
            keyword=keyword,
            log=self.log,
            done_callback=lambda _: self.set_status("搜索完成")
        )

    # ── 发布帖子 ──
    def on_publish(self):
        cfg = config.load()
        count = cfg.get("publish_count", 4)
        self.log(f"准备发布 {count} 篇帖子...")
        self.set_status("发布中...")
        tasks.publish_posts(
            count=count,
            log=self.log,
            done_callback=lambda ok: self.set_status(f"发布完成 ✅ {ok}/{count}")
        )

    # ── 获取评论 ──
    def on_comments(self):
        dialog = CommentDialog(on_confirm_cb=self._do_get_comments)
        dialog.open()

    def _do_get_comments(self, feed_id, xsec_token):
        self.log(f"获取评论: {feed_id[:8]}...")
        self.set_status("获取评论中...")
        tasks.get_comments(
            feed_id=feed_id,
            xsec_token=xsec_token,
            log=self.log,
            done_callback=lambda: self.set_status("评论获取完成")
        )


# ─────────────────────────────────────────────
# 设置界面
# ─────────────────────────────────────────────
class SettingsScreen(Screen):
    _sort_by    = StringProperty("最多点赞")
    _time_range = StringProperty("一周内")
    _pub_count  = NumericProperty(4)
    _platform   = StringProperty("xhs")

    def on_enter(self):
        """进入设置页面时加载当前配置"""
        cfg = config.load()

        # 关键词
        kws = cfg.get("hotspot_keywords", ["科技热点"])
        self.ids.keywords_input.text = ",".join(kws)

        # 排序 / 时间范围
        self._sort_by    = cfg.get("hotspot_sort_by", "最多点赞")
        self._time_range = cfg.get("hotspot_publish_time", "一周内")
        self._update_sort_buttons()
        self._update_time_buttons()

        # 发布数量
        self._pub_count = cfg.get("publish_count", 4)
        self._update_count_buttons()

        # 间隔
        self.ids.interval_input.text = str(cfg.get("publish_interval_seconds", 10))

        # 发布时间（改用 HH:MM 格式）
        pub_time = cfg.get("publish_scheduled_time", "09:00")
        if ":" in pub_time:
            hour, minute = pub_time.split(":")
            self.ids.publish_hour_input.text = hour
            self.ids.publish_minute_input.text = minute
        else:
            self.ids.publish_hour_input.text = str(cfg.get("publish_hour", 9))
            self.ids.publish_minute_input.text = str(cfg.get("publish_minute", 0))

        # 评论检查时间（改用 HH:MM 格式）
        comment_time = cfg.get("comment_check_time", "20:00")
        if ":" in comment_time:
            hour, minute = comment_time.split(":")
            self.ids.comment_hour_input.text = hour
            self.ids.comment_minute_input.text = minute
        else:
            self.ids.comment_hour_input.text = str(cfg.get("comment_check_hour", 20))
            self.ids.comment_minute_input.text = str(cfg.get("comment_check_minute", 0))

        # 平台选择
        self._platform = cfg.get("active_platform", "xhs")
        self._update_platform_buttons()

    # ── 选择按钮高亮辅助 ──
    def _highlight(self, widget_id, active):
        w = self.ids.get(widget_id)
        if w:
            COLOR_PRIMARY = (0.94, 0.22, 0.42, 1)
            COLOR_CARD    = (0.13, 0.13, 0.20, 1)
            # 通过 canvas 修改背景色
            w.background_color = COLOR_PRIMARY if active else COLOR_CARD

    def _update_sort_buttons(self):
        self._highlight("sort_zansu",  self._sort_by == "最多点赞")
        self._highlight("sort_newest", self._sort_by == "最新发布")

    def _update_time_buttons(self):
        self._highlight("time_week",  self._time_range == "一周内")
        self._highlight("time_month", self._time_range == "一个月内")
        self._highlight("time_all",   self._time_range == "不限")

    def _update_count_buttons(self):
        for i in range(1, 5):
            self._highlight(f"count_{i}", self._pub_count == i)

    def _update_platform_buttons(self):
        self._highlight("platform_xhs", self._platform == "xhs")
        self._highlight("platform_wechat", self._platform == "wechat")

    def set_sort(self, value):
        self._sort_by = value
        self._update_sort_buttons()

    def set_time_range(self, value):
        self._time_range = value
        self._update_time_buttons()

    def set_publish_count(self, value):
        self._pub_count = value
        self._update_count_buttons()

    def set_platform(self, value):
        self._platform = value
        self._update_platform_buttons()

    def save_settings(self):
        """读取所有输入框内容并保存"""
        kw_text = self.ids.keywords_input.text.strip()
        keywords = [k.strip() for k in kw_text.replace("，", ",").split(",") if k.strip()]
        if not keywords:
            keywords = ["科技热点"]

        def safe_int(widget_id, default, min_val=0, max_val=9999):
            try:
                v = int(self.ids[widget_id].text.strip())
                return max(min_val, min(max_val, v))
            except Exception:
                return default

        pub_hour = safe_int("publish_hour_input", 9, 0, 23)
        pub_minute = safe_int("publish_minute_input", 0, 0, 59)
        comment_hour = safe_int("comment_hour_input", 20, 0, 23)
        comment_minute = safe_int("comment_minute_input", 0, 0, 59)

        cfg = config.load()
        cfg.update({
            "hotspot_keywords":         keywords,
            "hotspot_sort_by":          self._sort_by,
            "hotspot_publish_time":     self._time_range,
            "publish_count":            int(self._pub_count),
            "publish_interval_seconds": safe_int("interval_input", 10, 1, 300),
            "publish_scheduled_time":   f"{pub_hour:02d}:{pub_minute:02d}",
            "comment_check_time":       f"{comment_hour:02d}:{comment_minute:02d}",
            "active_platform":          self._platform,
        })
        config.save(cfg)

        # 返回主界面
        App.get_running_app().goto_main()


# ─────────────────────────────────────────────
# App 主类
# ─────────────────────────────────────────────
class XhsApp(App):
    font_path = StringProperty("Roboto")  # 默认字体，启动时替换

    def build(self):
        self.title = "小红书运营工具箱"
        self._setup_font()
        self._setup_config_path()
        self._start_local_backend()

        sm = ScreenManager(transition=SlideTransition())
        sm.add_widget(MainScreen(name="main"))
        sm.add_widget(SettingsScreen(name="settings"))
        return sm

    def _setup_font(self):
        font = find_font()
        if font:
            try:
                LabelBase.register(name="XhsFont", fn_regular=font)
                self.font_path = "XhsFont"
                print(f"[Font] 已加载字体: {font}")
            except Exception as e:
                print(f"[Font] 字体加载失败: {e}")
        else:
            print("[Font] 未找到中文字体，使用默认字体")

    def _setup_config_path(self):
        """Android 下将配置文件路径指向 App 私有目录"""
        if kivy_platform == "android":
            from android.storage import app_storage_path  # type: ignore
            data_dir = app_storage_path()
            import core.config as cfg_module
            cfg_module._CONFIG_FILE = os.path.join(data_dir, "settings.json")

            # posts 目录也指向 assets
            from android.storage import primary_external_storage_path  # type: ignore
            import core.tasks as tasks_module
            tasks_module.POSTS_DIR = os.path.join(ROOT, "assets", "posts")

    def _start_local_backend(self):
        """启动本地后端服务"""
        try:
            from core import local_backend
            cfg = config.load()
            backend_mode = cfg.get("backend_mode", "local")
            
            if backend_mode == "local":
                if local_backend.start_backend(host="127.0.0.1", port=5000):
                    print("✅ 本地后端已启动: http://127.0.0.1:5000")
                else:
                    print("⚠️  本地后端启动失败，请检查 Flask 依赖")
        except Exception as e:
            print(f"⚠️  启动本地后端异常: {e}")

    def goto_settings(self):
        self.root.current = "settings"

    def goto_main(self):
        self.root.current = "main"


if __name__ == "__main__":
    XhsApp().run()
