#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tasks.py — 业务逻辑：搜索热点、发布帖子、查看评论
所有操作接受一个 log_callback(str) 参数用于向 UI 输出日志
"""

import json
import os
import time
import threading

from core import config, mcp_client

ASSETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
POSTS_DIR  = os.path.join(ASSETS_DIR, "posts")


# ─────────────────────────────────────────────
# 搜索热点
# ─────────────────────────────────────────────
def search_hotspot(keyword=None, log=print):
    cfg = config.load()
    if not keyword:
        keywords = cfg.get("hotspot_keywords", ["科技热点"])
        keyword = keywords[0] if keywords else "科技热点"

    log(f"🔍 搜索关键词: {keyword}")

    # 转换排序方式
    sort_map = {
        "最多点赞": "hot",
        "最新发布": "recent",
    }
    sort_by = sort_map.get(cfg.get("hotspot_sort_by", "最多点赞"), "hot")

    # 转换时间范围
    time_map = {
        "一周内": "week",
        "一个月内": "month",
        "不限": "all",
    }
    publish_time = time_map.get(cfg.get("hotspot_publish_time", "一周内"), "week")

    args = {
        "keyword": keyword,
        "filters": {
            "sort_by": sort_by,
            "note_type": cfg.get("hotspot_note_type", "图文"),
            "publish_time": publish_time,
        }
    }
    try:
        result = mcp_client.call_tool("search_feeds", args, timeout=60)
        if result.get("success"):
            feeds = result.get("data", {}).get("feeds", [])
            log(f"✅ 找到 {len(feeds)} 条热点内容")
            for feed in feeds[:5]:
                title = feed.get("title", "")
                likes = feed.get("interact_info", {}).get("like_count", 0)
                log(f"  - {title} (👍 {likes})")
        else:
            log(f"❌ 搜索失败: {result.get('error', '未知错误')}")
        return result
    except Exception as e:
        log(f"❌ 搜索失败: {e}")
        return None


def search_hotspot_async(keyword=None, log=print, done_callback=None):
    def _run():
        result = search_hotspot(keyword, log)
        if done_callback:
            done_callback(result)
    threading.Thread(target=_run, daemon=True).start()


# ─────────────────────────────────────────────
# 发布帖子
# ─────────────────────────────────────────────
def _load_post(filename):
    path = os.path.join(POSTS_DIR, filename)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _get_post_files():
    """返回所有可用帖子 (post_json, cover_jpg) 配对列表，按第1周顺序"""
    pairs = [
        ("post4_hotspot_315.json", "cover4_315.jpg",       "热点：315 AI投毒"),
        ("post1_cloud_explain.json", "cover1_cloud.jpg",   "云计算科普"),
        ("post2_ai_cloud.json",    "cover2_ai_cloud.jpg",  "ChatGPT背后的云"),
        ("post3_ai_life.json",     "cover3_ai_life.jpg",   "普通人用AI"),
    ]
    return pairs


def publish_posts(count=None, log=print, done_callback=None):
    """
    发布帖子
    :param count: 发布数量，None 则从配置读取
    """
    cfg = config.load()
    if count is None:
        count = cfg.get("publish_count", 4)
    count = max(1, min(4, int(count)))
    interval = cfg.get("publish_interval_seconds", 10)

    pairs = _get_post_files()[:count]

    def _run():
        log(f"🚀 开始发布，共 {count} 篇，间隔 {interval} 秒")
        success = 0
        for i, (post_fname, cover_fname, label) in enumerate(pairs):
            log(f"\n{'='*40}")
            log(f"📤 [{i+1}/{count}] {label}")
            post = _load_post(post_fname)
            if not post:
                log(f"❌ 找不到帖子文件: {post_fname}")
                continue

            # 检查封面图片
            cover_path = None
            if cover_fname:
                cover_path = os.path.join(POSTS_DIR, cover_fname)
                if not os.path.exists(cover_path):
                    # 封面可能在 assets/posts 外
                    cover_path = os.path.join(ASSETS_DIR, cover_fname)
                if not os.path.exists(cover_path):
                    cover_path = None

            args = {
                "title":   post.get("title", ""),
                "content": post.get("content", ""),
                "images":  [cover_path] if cover_path else [],
                "tags":    post.get("tags", []),
            }
            try:
                result = mcp_client.call_tool("publish_content", args, timeout=180)
                if result.get("success"):
                    note_id = result.get("data", {}).get("note_id", "未知")
                    note_url = result.get("data", {}).get("note_url", "")
                    log(f"✅ 第 {i+1} 篇发布成功 (ID: {note_id})")
                    if note_url:
                        log(f"   🔗 {note_url}")
                    success += 1
                else:
                    log(f"❌ 发布失败: {result.get('error', '未知错误')}")
            except Exception as e:
                log(f"❌ 发布失败: {e}")

            if i < len(pairs) - 1:
                log(f"⏳ 等待 {interval} 秒...")
                time.sleep(interval)

        log(f"\n🎉 完成！成功 {success}/{count} 篇")
        if done_callback:
            done_callback(success)

    threading.Thread(target=_run, daemon=True).start()


# ─────────────────────────────────────────────
# 获取评论
# ─────────────────────────────────────────────
def get_comments(feed_id, xsec_token=None, log=print, done_callback=None, platform="xhs"):
    def _run():
        log(f"💬 获取帖子评论: {feed_id}")
        args = {
            "feed_id": feed_id,
            "xsec_token": xsec_token,
            "platform": platform,
        }
        try:
            result = mcp_client.call_tool("get_feed_detail", args, timeout=60)
            if result.get("success"):
                comments = result.get("data", {}).get("comments", [])
                log(f"✅ 获取到 {len(comments)} 条评论")
                for comment in comments[:10]:
                    user = comment.get("user", {})
                    nickname = user.get("nickname", "匿名")
                    content = comment.get("content", "")
                    likes = comment.get("like_count", 0)
                    log(f"  - {nickname}: {content[:50]}... (👍 {likes})")
            else:
                log(f"❌ 获取失败: {result.get('error', '未知错误')}")
        except Exception as e:
            log(f"❌ 获取失败: {e}")
        if done_callback:
            done_callback()
    threading.Thread(target=_run, daemon=True).start()
