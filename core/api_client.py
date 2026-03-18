#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
core/api_client.py - REST API 客户端封装
"""

import json
import urllib.request
import urllib.error
from core import config


class APIClient:
    """REST API 客户端"""
    
    def __init__(self):
        self.base_url = config.get('api_url')
        self.user_id = config.get('user_id')
        self.timeout = 60
    
    def _request(self, method, endpoint, data=None, timeout=None):
        """发送请求"""
        if timeout is None:
            timeout = self.timeout
        
        url = f"{self.base_url}{endpoint}"
        headers = {
            "Content-Type": "application/json",
            "X-User-Id": self.user_id
        }
        
        payload = json.dumps(data).encode('utf-8') if data else None
        req = urllib.request.Request(url, data=payload, method=method)
        
        for k, v in headers.items():
            req.add_header(k, v)
        
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                response_data = resp.read().decode('utf-8')
                return json.loads(response_data)
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            raise Exception(f"HTTP {e.code}: {error_body}")
        except Exception as e:
            raise Exception(f"请求失败: {e}")
    
    def _post(self, endpoint, data=None, timeout=None):
        """POST 请求"""
        return self._request('POST', endpoint, data, timeout)
    
    def _get(self, endpoint, timeout=None):
        """GET 请求"""
        return self._request('GET', endpoint, None, timeout)
    
    # ─────────────────────────────────────────────
    # 配置接口
    # ─────────────────────────────────────────────
    
    def save_app_config(self, config_data):
        """保存应用配置"""
        return self._post('/config/app', config_data)
    
    def get_app_config(self):
        """获取应用配置"""
        return self._get('/config/app')
    
    def save_credentials(self, platform, credentials):
        """保存平台凭证"""
        return self._post('/config/credentials', {
            'platform': platform,
            'credentials': credentials
        })
    
    def get_credentials(self, platform):
        """获取平台凭证"""
        return self._get(f'/config/credentials/{platform}')
    
    # ─────────────────────────────────────────────
    # 内容接口
    # ─────────────────────────────────────────────
    
    def search_hotspot(self, keyword, filters=None):
        """搜索热点"""
        return self._post('/content/search-hotspot', {
            'keyword': keyword,
            'filters': filters or {}
        }, timeout=90)
    
    def publish_content(self, title, content, images=None, tags=None, platform=None):
        """发布内容"""
        return self._post('/content/publish', {
            'title': title,
            'content': content,
            'images': images or [],
            'tags': tags or [],
            'platform': platform
        }, timeout=180)
    
    def get_comments(self, post_id, platform=None):
        """获取评论"""
        url = f'/content/comments/{post_id}'
        if platform:
            url += f'?platform={platform}'
        return self._get(url, timeout=60)
    
    def get_publish_history(self, platform=None, limit=10):
        """获取发布历史"""
        url = f'/content/history?limit={limit}'
        if platform:
            url += f'&platform={platform}'
        return self._get(url, timeout=30)
    
    # ─────────────────────────────────────────────
    # 工具接口
    # ─────────────────────────────────────────────
    
    def health_check(self):
        """健康检查"""
        return self._get('/health')
    
    def list_platforms(self):
        """列出支持的平台"""
        return self._get('/platforms')
