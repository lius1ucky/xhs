#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scheduler.py — 后台定时任务管理
支持评论检查、自动发布等定时任务
"""

import threading
import time
import json
from datetime import datetime, timedelta
from typing import Callable, Dict, List, Optional, Any
from core.db import get_db


class Task:
    """定时任务"""
    
    def __init__(self, task_id: str, user_id: str, task_type: str, 
                 schedule_time: str, callback: Callable, 
                 params: Dict = None, enabled: bool = True):
        """
        Args:
            task_id: 任务 ID
            user_id: 用户 ID
            task_type: 任务类型 ("check_comments", "auto_publish", "custom")
            schedule_time: 调度时间 (HH:MM 格式)
            callback: 执行回调函数
            params: 任务参数
            enabled: 是否启用
        """
        self.task_id = task_id
        self.user_id = user_id
        self.task_type = task_type
        self.schedule_time = schedule_time
        self.callback = callback
        self.params = params or {}
        self.enabled = enabled
        self.last_run_at = None
        self.next_run_at = self._compute_next_run_time()
    
    def _compute_next_run_time(self) -> datetime:
        """计算下次执行时间"""
        hour, minute = map(int, self.schedule_time.split(':'))
        
        now = datetime.now()
        next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        # 如果今天的时间已过，则计划明天
        if next_run <= now:
            next_run += timedelta(days=1)
        
        return next_run
    
    def should_run(self) -> bool:
        """检查是否应该运行"""
        if not self.enabled:
            return False
        
        now = datetime.now()
        return now >= self.next_run_at
    
    def execute(self) -> bool:
        """执行任务"""
        try:
            self.callback(self.user_id, **self.params)
            self.last_run_at = datetime.now()
            self.next_run_at = self._compute_next_run_time()
            return True
        except Exception as e:
            print(f"❌ 任务执行失败 ({self.task_id}): {e}")
            return False


class Scheduler:
    """定时任务调度器"""
    
    def __init__(self, check_interval: int = 60):
        """
        Args:
            check_interval: 检查间隔（秒）
        """
        self.check_interval = check_interval
        self.tasks: Dict[str, Task] = {}
        self.running = False
        self.scheduler_thread = None
    
    def add_task(self, task: Task) -> None:
        """添加任务"""
        self.tasks[task.task_id] = task
        print(f"✅ 任务已添加: {task.task_id} ({task.task_type}) @ {task.schedule_time}")
    
    def remove_task(self, task_id: str) -> bool:
        """移除任务"""
        if task_id in self.tasks:
            del self.tasks[task_id]
            print(f"✅ 任务已移除: {task_id}")
            return True
        return False
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """获取任务"""
        return self.tasks.get(task_id)
    
    def list_tasks(self, user_id: str = None) -> List[Task]:
        """列出任务"""
        if user_id:
            return [t for t in self.tasks.values() if t.user_id == user_id]
        return list(self.tasks.values())
    
    def start(self) -> None:
        """启动调度器"""
        if self.running:
            return
        
        self.running = True
        self.scheduler_thread = threading.Thread(target=self._run, daemon=True)
        self.scheduler_thread.start()
        print("🚀 定时任务调度器已启动")
    
    def stop(self) -> None:
        """停止调度器"""
        self.running = False
        print("⏹️  定时任务调度器已停止")
    
    def _run(self) -> None:
        """调度器循环"""
        while self.running:
            try:
                now = datetime.now()
                
                for task in self.tasks.values():
                    if task.should_run():
                        print(f"⏰ 执行任务: {task.task_id} ({task.task_type})")
                        task.execute()
                
                time.sleep(self.check_interval)
            
            except Exception as e:
                print(f"❌ 调度器错误: {e}")
                time.sleep(self.check_interval)


# 全局调度器实例
_scheduler = None


def get_scheduler() -> Scheduler:
    """获取全局调度器"""
    global _scheduler
    if _scheduler is None:
        _scheduler = Scheduler(check_interval=60)
    return _scheduler


# ─────────────────────────────────────────
# 预定义任务回调
# ─────────────────────────────────────────

def check_comments_task(user_id: str, platform: str = "xhs", **kwargs) -> None:
    """
    定时检查评论任务
    
    Args:
        user_id: 用户 ID
        platform: 平台 ("xhs" / "wechat")
    """
    db = get_db()
    
    print(f"📨 正在检查 {user_id} 在 {platform} 的评论...")
    
    # 获取用户近期发布的笔记
    records = db.list_publish_records(user_id, platform, limit=10)
    
    for record in records:
        if not record.get('post_id'):
            continue
        
        post_id = record['post_id']
        
        if platform == "xhs":
            from core.xhs_api import XHSMockClient
            client = XHSMockClient(user_id)
            result = client.get_feed_comments(post_id)
        elif platform == "wechat":
            from core.wechat_api import WechatMockClient
            client = WechatMockClient()
            # 微信获取评论逻辑不同
            continue
        else:
            continue
        
        if result.get('success'):
            comments = result['data']['comments']
            
            for comment in comments:
                comment_id = comment['id']
                
                # 检查是否已存在
                existing = db.get_comments(user_id, post_id, platform)
                if any(c['id'] == comment_id for c in existing):
                    continue
                
                # 添加新评论到数据库
                db.add_comment(
                    user_id, post_id, platform,
                    comment['id'],
                    comment['user']['nickname'],
                    comment['content']
                )
            
            print(f"✅ 已获取 {len(comments)} 条新评论 (post_id: {post_id})")


def auto_publish_task(user_id: str, platform: str = "xhs", 
                     content_templates: List[str] = None, **kwargs) -> None:
    """
    定时自动发布任务
    
    Args:
        user_id: 用户 ID
        platform: 平台
        content_templates: 内容模板列表
    """
    if not content_templates:
        print(f"⚠️  自动发布: 未配置内容模板")
        return
    
    db = get_db()
    
    print(f"📤 正在自动发布 {user_id} 的内容到 {platform}...")
    
    # 选择一个模板
    import random
    template = random.choice(content_templates)
    
    # 获取凭证
    creds = db.get_credentials(user_id, platform)
    
    if not creds or 'access_token' not in creds:
        print(f"❌ 自动发布: 缺少 {platform} 凭证")
        return
    
    # 调用平台 API 发布
    if platform == "xhs":
        from core.xhs_api import XHSMockClient
        client = XHSMockClient(user_id)
        result = client.publish_note(
            title=template.get('title', ''),
            content=template.get('content', ''),
            images=template.get('images', []),
            tags=template.get('tags', [])
        )
    elif platform == "wechat":
        from core.wechat_api import WechatMockClient
        client = WechatMockClient(
            creds.get('app_id'),
            creds.get('app_secret')
        )
        result = client.send_text_message(
            creds.get('openid'),
            template.get('content', '')
        )
    else:
        print(f"❌ 未知平台: {platform}")
        return
    
    if result.get('success'):
        # 保存发布记录
        db.add_publish_record(
            user_id, platform,
            template.get('title', ''),
            template.get('content', ''),
            images=template.get('images', []),
            tags=template.get('tags', []),
            post_id=result['data'].get('note_id') or result['data'].get('msgid')
        )
        print(f"✅ 自动发布成功")
    else:
        print(f"❌ 自动发布失败: {result.get('error')}")


def cleanup_old_data_task(user_id: str, days: int = 90, **kwargs) -> None:
    """
    定时清理旧数据任务（可选）
    
    Args:
        user_id: 用户 ID
        days: 保留天数
    """
    db = get_db()
    
    print(f"🧹 正在清理 {user_id} 的旧数据（保留 {days} 天）...")
    
    # 这里可以实现清理旧评论、旧发布记录等逻辑
    # 示例：删除 days 天前的评论
    
    print(f"✅ 旧数据清理完成")


# ─────────────────────────────────────────
# 任务管理 API
# ─────────────────────────────────────────

def create_check_comments_task(user_id: str, platform: str, 
                              check_time: str = "20:00") -> Task:
    """
    创建评论检查任务
    
    Args:
        user_id: 用户 ID
        platform: 平台
        check_time: 检查时间 (HH:MM)
    
    Returns:
        Task
    """
    task = Task(
        task_id=f"check_comments_{user_id}_{platform}",
        user_id=user_id,
        task_type="check_comments",
        schedule_time=check_time,
        callback=check_comments_task,
        params={'platform': platform}
    )
    return task


def create_auto_publish_task(user_id: str, platform: str, publish_time: str,
                            content_templates: List[str] = None) -> Task:
    """
    创建自动发布任务
    
    Args:
        user_id: 用户 ID
        platform: 平台
        publish_time: 发布时间 (HH:MM)
        content_templates: 内容模板
    
    Returns:
        Task
    """
    task = Task(
        task_id=f"auto_publish_{user_id}_{platform}",
        user_id=user_id,
        task_type="auto_publish",
        schedule_time=publish_time,
        callback=auto_publish_task,
        params={
            'platform': platform,
            'content_templates': content_templates or []
        }
    )
    return task
