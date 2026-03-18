#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
config.py — 用户配置管理
读写 settings.json，提供默认值
支持 REST API 后端和 MCP Server 两种模式
"""

import json
import os

# 配置文件存放在 App 数据目录
_CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "settings.json")

DEFAULTS = {
    # 后端配置（本地后端自动启动）
    "backend_mode": "local",  # 'local' 或 'remote'
    "api_url": "http://127.0.0.1:5000/api",  # 本地 API 地址（也是默认值）
    "user_id": "local_user",  # 用户 ID，用于后端识别
    
    # 平台选择
    "active_platform": "xhs",  # 'xhs' 或 'wechat'
    
    # 热点搜索
    "hotspot_keywords": ["科技热点", "AI工具", "云计算"],   # 关键词列表
    "hotspot_sort_by": "最多点赞",
    "hotspot_note_type": "图文",
    "hotspot_publish_time": "一周内",

    # 发布设置
    "publish_count": 4,               # 每次发布文章数量 1~4
    "publish_interval_seconds": 10,   # 每篇间隔秒数
    "publish_scheduled_time": "09:00",  # 定时发布时间 (HH:MM)

    # 评论互动
    "comment_check_time": "20:00",    # 每天几点检查评论 (HH:MM)
    "comment_auto_reply": False,      # 是否自动回复（预留）

    # MCP Server（仅当 backend_mode=mcp 时使用）
    "mcp_url": "http://localhost:18060/mcp",
    "mcp_timeout": 180,
    
    # 平台凭证（使用 REST API 时通过配置界面设置）
    "xhs_credentials": {},  # 小红书凭证
    "wechat_credentials": {},  # 微信公众号凭证
}


def load() -> dict:
    """加载配置，缺失字段用默认值补全"""
    cfg = dict(DEFAULTS)
    if os.path.exists(_CONFIG_FILE):
        try:
            with open(_CONFIG_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
            cfg.update(saved)
        except Exception:
            pass
    return cfg


def save(cfg: dict):
    """保存配置到文件"""
    with open(_CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


def get(key: str):
    """获取单个配置项"""
    return load().get(key, DEFAULTS.get(key))


def set_value(key: str, value):
    """设置单个配置项"""
    cfg = load()
    cfg[key] = value
    save(cfg)
