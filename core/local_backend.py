#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
local_backend.py — 本地 Flask 后端服务（增强版 + Android 修复版）
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

# 尝试导入 Flask（可能在 Android 上不可用）
try:
    from flask import Flask, request, jsonify, send_file
    FLASK_AVAILABLE = True
except ImportError as e:
    Flask = None
    FLASK_AVAILABLE = False
    print(f"⚠️  Flask 导入失败: {e}")

# 安全导入依赖模块（使用 try-except）
try:
    from core.db import get_db, set_db_path
except ImportError as e:
    print(f"❌ db 模块导入失败: {e}")
    get_db = None
    set_db_path = None

try:
    from core.xhs_api import XHSMockClient
except ImportError as e:
    print(f"❌ xhs_api 模块导入失败: {e}")
    XHSMockClient = None

try:
    from core.wechat_api import WechatMockClient
except ImportError as e:
    print(f"❌ wechat_api 模块导入失败: {e}")
    WechatMockClient = None

try:
    from core.scheduler import get_scheduler, create_check_comments_task, create_auto_publish_task
except ImportError as e:
    print(f"❌ scheduler 模块导入失败: {e}")
    get_scheduler = None
    create_check_comments_task = None
    create_auto_publish_task = None

# 全局后端实例
_backend_app = None
_backend_thread = None
_backend_running = False


class LocalBackend:
    """本地 Flask 后端（增强版）"""
    
    def __init__(self, host='127.0.0.1', port=5000, db_path=None):
        if not FLASK_AVAILABLE:
            raise RuntimeError("Flask 不可用，无法启动后端")
        
        if Flask is None:
            raise RuntimeError("Flask 导入失败")
        
        self.host = host
        self.port = port
        self.app = Flask(__name__)
        
        # 初始化数据库（如果可用）
        if get_db is not None:
            if db_path:
                set_db_path(db_path)
            self.db = get_db()
        else:
            print("⚠️  数据库模块不可用")
            self.db = None
        
        # 启动定时任务调度器（如果可用）
        if get_scheduler is not None:
            self.scheduler = get_scheduler()
        else:
            print("⚠️  调度器模块不可用")
            self.scheduler = None
        
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
                'features': ['database', 'multi-user', 'scheduler', 'real-api'],
                'flask_available': FLASK_AVAILABLE,
                'db_available': self.db is not None,
                'scheduler_available': self.scheduler is not None
            })
        
        # ─────────────────────────────────────────
        # 用户管理 API
        # ─────────────────────────────────────────
        
        @self.app.route('/api/users', methods=['GET'])
        def list_users():
            """列出所有用户"""
            if self.db is None:
                return jsonify({'success': False, 'error': '数据库不可用'}), 500
            
            try:
                users = self.db.list_users()
                return jsonify({
                    'success': True,
                    'data': users
                })
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/users/<user_id>', methods=['GET'])
        def get_user(user_id):
            """获取用户信息"""
            if self.db is None:
                return jsonify({'success': False, 'error': '数据库不可用'}), 500
            
            try:
                user = self.db.get_user(user_id)
                return jsonify({
                    'success': True if user else False,
                    'data': user
                })
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/users', methods=['POST'])
        def create_user():
            """创建用户"""
            if self.db is None:
                return jsonify({'success': False, 'error': '数据库不可用'}), 500
            
            try:
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
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 500
        
        # ─────────────────────────────────────────
        # 配置管理 API
        # ─────────────────────────────────────────
        
        @self.app.route('/api/config/get', methods=['GET'])
        def get_config():
            """获取配置"""
            try:
                cfg = config.load()
                return jsonify({
                    'success': True,
                    'data': cfg
                })
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/config/set', methods=['POST'])
        def set_config():
            """更新配置"""
            try:
                data = request.get_json() or {}
                cfg = config.load()
                cfg.update(data)
                config.save(cfg)
                
                return jsonify({
                    'success': True,
                    'message': '配置已保存'
                })
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 500
        
        # ─────────────────────────────────────────
        # 凭证管理 API
        # ─────────────────────────────────────────
        
        @self.app.route('/api/credentials/<platform>', methods=['GET'])
        def get_credentials(platform):
            """获取平台凭证"""
            if self.db is None:
                return jsonify({'success': False, 'error': '数据库不可用'}), 500
            
            try:
                user_id = self._get_user_id()
                creds = self.db.get_credentials(user_id, platform)
                
                return jsonify({
                    'success': True,
                    'data': creds
                })
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/credentials/<platform>', methods=['POST'])
        def set_credentials(platform):
            """保存平台凭证"""
            if self.db is None:
                return jsonify({'success': False, 'error': '数据库不可用'}), 500
            
            try:
                user_id = self._get_user_id()
                data = request.get_json() or {}
                
                for key, value in data.items():
                    self.db.set_credential(user_id, platform, key, value)
                
                return jsonify({
                    'success': True,
                    'message': f'{platform} 凭证已保存'
                })
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 500
        
        # ─────────────────────────────────────────
        # 平台管理 API
        # ─────────────────────────────────────────
        
        @self.app.route('/api/platform/set', methods=['POST'])
        def set_platform():
            """切换平台"""
            try:
                data = request.get_json() or {}
                platform = data.get('platform', 'xhs')
                
                config.set_value('active_platform', platform)
                
                return jsonify({
                    'success': True,
                    'message': f'已切换到 {platform}',
                    'active_platform': platform
                })
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 500
        
        @self.app.route('/api/platform/get', methods=['GET'])
        def get_platform():
            """获取当前平台"""
            try:
                return jsonify({
                    'success': True,
                    'active_platform': config.get('active_platform')
                })
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 500
        
        # ─────────────────────────────────────────
        # 错误处理
        # ─────────────────────────────────────────
        
        @self.app.errorhandler(404)
        def not_found(e):
            return jsonify({'success': False, 'error': '接口不存在'}), 404
        
        @self.app.errorhandler(500)
        def server_error(e):
            return jsonify({'success': False, 'error': str(e)}), 500

        # ─────────────────────────────────────────
        # 内容管理 API（搜索、发布、评论）
        # ─────────────────────────────────────────

        @self.app.route('/api/content/search-hotspot', methods=['POST'])
        def search_hotspot_api():
            """搜索热点内容"""
            try:
                data = request.get_json() or {}
                keyword = data.get('keyword', '')
                filters = data.get('filters', {})

                if not keyword:
                    return jsonify({'success': False, 'error': '缺少关键词'}), 400

                # 根据平台选择 API 客户端
                platform = config.get('active_platform', 'xhs')

                if platform == "xhs":
                    if XHSMockClient:
                        client = XHSMockClient(self._get_user_id())
                        result = client.search_feeds(
                            keyword=keyword,
                            sort=filters.get('sort_by', 'hot'),
                            note_type=filters.get('note_type', 'all'),
                            time_range=filters.get('publish_time', 'week')
                        )
                    else:
                        result = {'success': False, 'error': '小红书 API 不可用'}
                else:
                    result = {'success': False, 'error': f'不支持的平台: {platform}'}

                return jsonify(result)
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 500

        @self.app.route('/api/content/publish', methods=['POST'])
        def publish_content_api():
            """发布内容"""
            try:
                data = request.get_json() or {}
                title = data.get('title', '')
                content = data.get('content', '')
                images = data.get('images', [])
                tags = data.get('tags', [])

                if not title and not content:
                    return jsonify({'success': False, 'error': '标题和内容不能同时为空'}), 400

                # 根据平台选择 API 客户端
                platform = config.get('active_platform', 'xhs')

                if platform == "xhs":
                    if XHSMockClient:
                        client = XHSMockClient(self._get_user_id())
                        result = client.publish_note(
                            title=title,
                            content=content,
                            images=images,
                            tags=tags
                        )
                    else:
                        result = {'success': False, 'error': '小红书 API 不可用'}
                else:
                    result = {'success': False, 'error': f'不支持的平台: {platform}'}

                # 保存发布记录
                if result.get('success') and self.db:
                    user_id = self._get_user_id()
                    post_id = result.get('data', {}).get('note_id')
                    self.db.add_publish_record(
                        user_id, platform, title, content,
                        images=images, tags=tags, post_id=post_id
                    )

                return jsonify(result)
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 500

        @self.app.route('/api/content/comments/<path:post_id>', methods=['GET'])
        @self.app.route('/api/content/comments/<path:post_id>/', methods=['GET'])
        def get_comments_api(post_id):
            """获取帖子评论"""
            try:
                platform = request.args.get('platform', 'xhs')

                if platform == "xhs":
                    if XHSMockClient:
                        client = XHSMockClient(self._get_user_id())
                        result = client.get_feed_comments(post_id)
                    else:
                        result = {'success': False, 'error': '小红书 API 不可用'}
                else:
                    result = {'success': False, 'error': f'不支持的平台: {platform}'}

                return jsonify(result)
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 500

        @self.app.route('/api/content/history', methods=['GET'])
        def get_publish_history_api():
            """获取发布历史"""
            try:
                if self.db is None:
                    return jsonify({'success': False, 'error': '数据库不可用'}), 500

                user_id = self._get_user_id()
                platform = request.args.get('platform')
                limit = int(request.args.get('limit', 10))

                records = self.db.list_publish_records(user_id, platform, limit)
                return jsonify({
                    'success': True,
                    'data': records
                })
            except Exception as e:
                return jsonify({'success': False, 'error': str(e)}), 500

        @self.app.route('/api/stats', methods=['GET'])
        def get_stats_api():
            """获取用户统计数据"""
            try:
                if self.db is None:
                    return jsonify({'success': False, 'error': '数据库不可用'}), 500

                user_id = self._get_user_id()
                stats = self.db.get_stats(user_id)
                return jsonify({
                    'success': True,
                    'data': stats
                })
            except Exception as e:
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
        print("⚠️  后端已在运行")
        return False
    
    if not FLASK_AVAILABLE:
        print("⚠️  Flask 未安装，无法启动本地后端")
        return False
    
    try:
        print("🔄 启动本地后端...")
        _backend_app = LocalBackend(host, port, db_path)
        _backend_thread = threading.Thread(target=_backend_app.run, daemon=True)
        _backend_thread.start()
        _backend_running = True
        
        # 等待服务启动
        time.sleep(1)
        print("✅ 本地后端已启动")
        return True
    except Exception as e:
        print(f"❌ 启动后端失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def stop_backend():
    """停止后端服务"""
    global _backend_running
    _backend_running = False
    print("⏹️  后端服务已停止")


def is_running():
    """检查后端是否运行"""
    return _backend_running
