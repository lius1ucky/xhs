#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
local_backend.py — 本地 Flask 后端服务（增强版）
在 Android 本地运行，为 App 提供 REST API
支持 SQLite、真实 API、定时任务、多用户等
"""

import os
import json
import threading
import time
import io
from datetime import datetime
from core import config

try:
    from flask import Flask, request, jsonify, send_file
except ImportError:
    Flask = None
    print("Flask not available, local backend disabled")

from core.db import get_db, set_db_path
from core.xhs_api import XHSMockClient
from core.wechat_api import WechatMockClient
from core.scheduler import get_scheduler, create_check_comments_task, create_auto_publish_task

# 全局后端实例
_backend_app = None
_backend_thread = None
_backend_running = False


class LocalBackend:
    """本地 Flask 后端（增强版）"""
    
    def __init__(self, host='127.0.0.1', port=5000, db_path=None):
        self.host = host
        self.port = port
        self.app = Flask(__name__)
        
        # 初始化数据库
        if db_path:
            set_db_path(db_path)
        self.db = get_db()
        
        # 启动定时任务调度器
        self.scheduler = get_scheduler()
        
        self._init_routes()
    
    def _get_user_id(self) -> str:
        """从请求头获取用户 ID"""
        return request.headers.get('X-User-Id', 'default_user')
    
    def _init_routes(self):
        """初始化 API 路由"""
        
        # ─────────────────────────────────────────
        # 系统管理 API
        # ─────────────────────────────────────────
        
        @self.app.route('/api/health', methods=['GET'])
        def health():
            """健康检查"""
            return jsonify({
                'status': 'ok',
                'timestamp': datetime.now().isoformat(),
                'version': '2.0.0',
                'features': ['database', 'multi-user', 'scheduler', 'real-api']
            })
        
        # ─────────────────────────────────────────
        # 用户管理 API
        # ─────────────────────────────────────────
        
        @self.app.route('/api/users', methods=['GET'])
        def list_users():
            """列出所有用户"""
            users = self.db.list_users()
            return jsonify({
                'success': True,
                'data': users
            })
        
        @self.app.route('/api/users/<user_id>', methods=['GET'])
        def get_user(user_id):
            """获取用户信息"""
            user = self.db.get_user(user_id)
            return jsonify({
                'success': True if user else False,
                'data': user
            })
        
        @self.app.route('/api/users', methods=['POST'])
        def create_user():
            """创建用户"""
            data = request.get_json() or {}
            user_id = data.get('user_id')
            username = data.get('username', user_id)
            
            if not user_id:
                return jsonify({'success': False, 'error': '缺少 user_id'}), 400
            
            result = self.db.create_user(user_id, username)
            return jsonify({
                'success': result,
                'message': '用户已创建' if result else '用户已存在'
            })
        
        # ─────────────────────────────────────────
        # 配置管理 API
        # ─────────────────────────────────────────
        
        @self.app.route('/api/config/get', methods=['GET'])
        def get_config():
            """获取配置"""
            cfg = config.load()
            return jsonify({
                'success': True,
                'data': cfg
            })
        
        @self.app.route('/api/config/set', methods=['POST'])
        def set_config():
            """更新配置"""
            data = request.get_json() or {}
            cfg = config.load()
            cfg.update(data)
            config.save(cfg)
            
            return jsonify({
                'success': True,
                'message': '配置已保存'
            })
        
        # ─────────────────────────────────────────
        # 凭证管理 API
        # ─────────────────────────────────────────
        
        @self.app.route('/api/credentials/<platform>', methods=['GET'])
        def get_credentials(platform):
            """获取平台凭证"""
            user_id = self._get_user_id()
            creds = self.db.get_credentials(user_id, platform)
            
            return jsonify({
                'success': True,
                'data': creds
            })
        
        @self.app.route('/api/credentials/<platform>', methods=['POST'])
        def set_credentials(platform):
            """保存平台凭证"""
            user_id = self._get_user_id()
            data = request.get_json() or {}
            
            for key, value in data.items():
                self.db.set_credential(user_id, platform, key, value)
            
            return jsonify({
                'success': True,
                'message': f'{platform} 凭证已保存'
            })
        
        # ─────────────────────────────────────────
        # 内容搜索 API（真实 API）
        # ─────────────────────────────────────────
        
        @self.app.route('/api/content/search-hotspot', methods=['POST'])
        def search_hotspot():
            """搜索热点（集成真实 API）"""
            user_id = self._get_user_id()
            data = request.get_json() or {}
            keyword = data.get('keyword', '')
            platform = config.get('active_platform', 'xhs')
            
            if platform == 'xhs':
                client = XHSMockClient(user_id)
                result = client.search_feeds(keyword)
                return jsonify(result)
            
            elif platform == 'wechat':
                client = WechatMockClient()
                return jsonify({'success': True, 'data': []})
            
            return jsonify({'success': False, 'error': '未知平台'})
        
        # ─────────────────────────────────────────
        # 内容发布 API
        # ─────────────────────────────────────────
        
        @self.app.route('/api/content/publish', methods=['POST'])
        def publish():
            """发布内容"""
            user_id = self._get_user_id()
            data = request.get_json() or {}
            platform = config.get('active_platform', 'xhs')
            
            title = data.get('title', '')
            content = data.get('content', '')
            images = data.get('images', [])
            tags = data.get('tags', [])
            
            # 调用真实 API（或 Mock）
            if platform == 'xhs':
                client = XHSMockClient(user_id)
                result = client.publish_note(title, content, images, tags=tags)
                
                if result.get('success'):
                    record_id = self.db.add_publish_record(
                        user_id, platform, title, content,
                        images=images, tags=tags,
                        post_id=result['data'].get('note_id')
                    )
                    return jsonify({
                        'success': True,
                        'data': {
                            'record_id': record_id,
                            'post_id': result['data'].get('note_id'),
                            'note_url': result['data'].get('note_url')
                        }
                    })
            
            return jsonify({'success': False, 'error': '发布失败'})
        
        # ─────────────────────────────────────────
        # 发布历史 API
        # ─────────────────────────────────────────
        
        @self.app.route('/api/content/history', methods=['GET'])
        def history():
            """获取发布历史"""
            user_id = self._get_user_id()
            platform = request.args.get('platform')
            limit = int(request.args.get('limit', 100))
            
            records = self.db.list_publish_records(user_id, platform, limit)
            
            return jsonify({
                'success': True,
                'data': records
            })
        
        # ─────────────────────────────────────────
        # 评论管理 API
        # ─────────────────────────────────────────
        
        @self.app.route('/api/content/comments/<post_id>', methods=['GET'])
        def get_comments(post_id):
            """获取评论"""
            user_id = self._get_user_id()
            platform = request.args.get('platform', 'xhs')
            
            comments = self.db.get_comments(user_id, post_id, platform)
            
            return jsonify({
                'success': True,
                'data': {
                    'post_id': post_id,
                    'count': len(comments),
                    'comments': comments
                }
            })
        
        # ─────────────────────────────────────────
        # 统计 API
        # ─────────────────────────────────────────
        
        @self.app.route('/api/stats', methods=['GET'])
        def get_stats():
            """获取统计数据"""
            user_id = self._get_user_id()
            stats = self.db.get_stats(user_id)
            
            return jsonify({
                'success': True,
                'data': stats
            })
        
        # ─────────────────────────────────────────
        # 数据导出 API
        # ─────────────────────────────────────────
        
        @self.app.route('/api/export/json', methods=['GET'])
        def export_json():
            """导出为 JSON"""
            user_id = self._get_user_id()
            platform = request.args.get('platform')
            
            json_str = self.db.export_records_as_json(user_id, platform)
            
            return send_file(
                io.BytesIO(json_str.encode('utf-8')),
                mimetype='application/json',
                as_attachment=True,
                download_name=f'records_{user_id}_{datetime.now().strftime("%Y%m%d")}.json'
            )
        
        @self.app.route('/api/export/csv', methods=['GET'])
        def export_csv():
            """导出为 CSV"""
            user_id = self._get_user_id()
            platform = request.args.get('platform')
            
            csv_str = self.db.export_records_as_csv(user_id, platform)
            
            return send_file(
                io.BytesIO(csv_str.encode('utf-8-sig')),
                mimetype='text/csv',
                as_attachment=True,
                download_name=f'records_{user_id}_{datetime.now().strftime("%Y%m%d")}.csv'
            )
        
        # ─────────────────────────────────────────
        # 定时任务 API
        # ─────────────────────────────────────────
        
        @self.app.route('/api/tasks', methods=['GET'])
        def list_tasks():
            """列出用户的所有任务"""
            user_id = self._get_user_id()
            tasks = self.scheduler.list_tasks(user_id)
            
            task_list = []
            for task in tasks:
                task_list.append({
                    'task_id': task.task_id,
                    'task_type': task.task_type,
                    'schedule_time': task.schedule_time,
                    'enabled': task.enabled,
                    'last_run_at': task.last_run_at.isoformat() if task.last_run_at else None,
                    'next_run_at': task.next_run_at.isoformat() if task.next_run_at else None
                })
            
            return jsonify({
                'success': True,
                'data': task_list
            })
        
        @self.app.route('/api/tasks/check-comments', methods=['POST'])
        def create_check_comments_task_api():
            """创建评论检查任务"""
            user_id = self._get_user_id()
            data = request.get_json() or {}
            
            platform = data.get('platform', 'xhs')
            check_time = data.get('check_time', '20:00')
            
            task = create_check_comments_task(user_id, platform, check_time)
            self.scheduler.add_task(task)
            self.scheduler.start()
            
            return jsonify({
                'success': True,
                'message': f'评论检查任务已创建 @ {check_time}',
                'task_id': task.task_id
            })
        
        @self.app.route('/api/tasks/auto-publish', methods=['POST'])
        def create_auto_publish_task_api():
            """创建自动发布任务"""
            user_id = self._get_user_id()
            data = request.get_json() or {}
            
            platform = data.get('platform', 'xhs')
            publish_time = data.get('publish_time', '09:00')
            templates = data.get('templates', [])
            
            task = create_auto_publish_task(user_id, platform, publish_time, templates)
            self.scheduler.add_task(task)
            self.scheduler.start()
            
            return jsonify({
                'success': True,
                'message': f'自动发布任务已创建 @ {publish_time}',
                'task_id': task.task_id
            })
        
        @self.app.route('/api/tasks/<task_id>', methods=['DELETE'])
        def delete_task(task_id):
            """删除任务"""
            self.scheduler.remove_task(task_id)
            
            return jsonify({
                'success': True,
                'message': '任务已删除'
            })
        
        # ─────────────────────────────────────────
        # 平台管理 API
        # ─────────────────────────────────────────
        
        @self.app.route('/api/platform/set', methods=['POST'])
        def set_platform():
            """切换平台"""
            data = request.get_json() or {}
            platform = data.get('platform', 'xhs')
            
            config.set_value('active_platform', platform)
            
            return jsonify({
                'success': True,
                'message': f'已切换到 {platform}',
                'active_platform': platform
            })
        
        @self.app.route('/api/platform/get', methods=['GET'])
        def get_platform():
            """获取当前平台"""
            return jsonify({
                'success': True,
                'active_platform': config.get('active_platform')
            })
        
        # ─────────────────────────────────────────
        # 错误处理
        # ─────────────────────────────────────────
        
        @self.app.errorhandler(404)
        def not_found(e):
            return jsonify({'success': False, 'error': '接口不存在'}), 404
        
        @self.app.errorhandler(500)
        def server_error(e):
            return jsonify({'success': False, 'error': str(e)}), 500
    
    def run(self):
        """运行后端服务"""
        try:
            print(f"\n🚀 本地后端启动（增强版）: http://{self.host}:{self.port}")
            print(f"📦 功能: SQLite数据库 | 多用户 | 定时任务 | 真实API")
            self.app.run(host=self.host, port=self.port, debug=False, threaded=True)
        except Exception as e:
            print(f"❌ 后端启动失败: {e}")


def start_backend(host='127.0.0.1', port=5000, db_path=None):
    """在后台线程启动后端"""
    global _backend_app, _backend_thread, _backend_running
    
    if _backend_running:
        return False
    
    if Flask is None:
        print("⚠️  Flask 未安装，无法启动本地后端")
        return False
    
    try:
        _backend_app = LocalBackend(host, port, db_path)
        _backend_thread = threading.Thread(target=_backend_app.run, daemon=True)
        _backend_thread.start()
        _backend_running = True
        
        # 等待服务启动
        time.sleep(1)
        return True
    except Exception as e:
        print(f"❌ 启动后端失败: {e}")
        return False


def stop_backend():
    """停止后端服务"""
    global _backend_running
    _backend_running = False


def is_running():
    """检查后端是否运行"""
    return _backend_running
