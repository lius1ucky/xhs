#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
xhs_api.py — 真实小红书 API 集成
基于小红书官方 API，支持搜索、发布、评论获取等功能
"""

import json
import time
import hashlib
import hmac
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime
from typing import Dict, List, Optional, Any


class XHSAPIClient:
    """小红书 API 客户端"""
    
    # 小红书官方 API 端点（需要申请）
    API_HOST = "https://api.xiaohongshu.com"
    API_VERSION = "v1"
    
    def __init__(self, access_token: str, user_id: str = None):
        """
        初始化客户端
        
        Args:
            access_token: 小红书开放平台 token（通过 OAuth 获取）
            user_id: 用户 ID
        """
        self.access_token = access_token
        self.user_id = user_id
    
    def _http_request(self, method: str, endpoint: str, params: Dict = None, 
                     data: Dict = None, timeout: int = 30) -> Dict:
        """发送 HTTP 请求到小红书 API"""
        url = f"{self.API_HOST}/{self.API_VERSION}{endpoint}"
        
        # 添加认证参数
        if params is None:
            params = {}
        params['access_token'] = self.access_token
        
        if method == "GET":
            query_string = urllib.parse.urlencode(params)
            url += f"?{query_string}"
            try:
                with urllib.request.urlopen(url, timeout=timeout) as resp:
                    return json.loads(resp.read().decode('utf-8'))
            except urllib.error.HTTPError as e:
                error_body = e.read().decode('utf-8')
                return {'success': False, 'error': f"HTTP {e.code}: {error_body}"}
        
        elif method == "POST":
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.access_token}'
            }
            payload = json.dumps(data or {}).encode('utf-8')
            
            req = urllib.request.Request(url, data=payload, headers=headers, method=method)
            try:
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    return json.loads(resp.read().decode('utf-8'))
            except urllib.error.HTTPError as e:
                error_body = e.read().decode('utf-8')
                return {'success': False, 'error': f"HTTP {e.code}: {error_body}"}
    
    # ─────────────────────────────────────────
    # 搜索 API
    # ─────────────────────────────────────────
    
    def search_feeds(self, keyword: str, sort: str = "hot", 
                    note_type: str = "all", time_range: str = "week",
                    page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """
        搜索笔记/热点
        
        Args:
            keyword: 搜索关键词
            sort: 排序方式 ("hot" / "recent" / "popular")
            note_type: 笔记类型 ("all" / "图文" / "视频")
            time_range: 时间范围 ("week" / "month" / "all")
            page: 页码
            page_size: 每页数量
        
        Returns:
            {
                'success': bool,
                'data': {
                    'feeds': [...],
                    'total': int,
                    'has_more': bool
                }
            }
        """
        params = {
            'keyword': keyword,
            'sort': sort,
            'note_type': note_type,
            'time_range': time_range,
            'page': page,
            'page_size': page_size,
        }
        
        resp = self._http_request('GET', '/feeds/search', params=params)
        
        if 'data' in resp and 'feeds' in resp['data']:
            return {
                'success': True,
                'data': {
                    'feeds': [self._parse_feed(f) for f in resp['data']['feeds']],
                    'total': resp['data'].get('total', 0),
                    'has_more': resp['data'].get('has_more', False)
                }
            }
        
        return resp
    
    def _parse_feed(self, feed: Dict) -> Dict:
        """解析笔记信息"""
        return {
            'id': feed.get('id'),
            'title': feed.get('title'),
            'desc': feed.get('desc'),
            'type': feed.get('type'),  # 图文、视频等
            'interact_info': feed.get('interact_info', {}),
            'user': feed.get('user', {}),
            'create_time': feed.get('create_time'),
            'image_list': feed.get('image_list', []),
        }
    
    # ─────────────────────────────────────────
    # 发布 API
    # ─────────────────────────────────────────
    
    def publish_note(self, title: str, content: str, images: List[str] = None,
                    video: str = None, tags: List[str] = None, 
                    at_users: List[str] = None) -> Dict[str, Any]:
        """
        发布笔记
        
        Args:
            title: 标题
            content: 内容
            images: 图片 URL 列表
            video: 视频 URL
            tags: 标签列表
            at_users: @用户列表
        
        Returns:
            {
                'success': bool,
                'data': {
                    'note_id': str,
                    'note_url': str
                }
            }
        """
        payload = {
            'title': title,
            'content': content,
            'note_type': 'video' if video else 'normal',
        }
        
        if images:
            payload['images'] = images
        
        if video:
            payload['video'] = video
        
        if tags:
            payload['tags'] = tags
        
        if at_users:
            payload['at_users'] = at_users
        
        resp = self._http_request('POST', '/notes/publish', data=payload, timeout=60)
        
        if 'data' in resp and 'note_id' in resp['data']:
            return {
                'success': True,
                'data': {
                    'note_id': resp['data']['note_id'],
                    'note_url': f"https://xiaohongshu.com/explore/{resp['data']['note_id']}"
                }
            }
        
        return resp
    
    # ─────────────────────────────────────────
    # 评论 API
    # ─────────────────────────────────────────
    
    def get_feed_comments(self, feed_id: str, page: int = 1, 
                         page_size: int = 20, sort: str = "hot") -> Dict[str, Any]:
        """
        获取笔记评论
        
        Args:
            feed_id: 笔记 ID
            page: 页码
            page_size: 每页数量
            sort: 排序方式 ("hot" / "recent")
        
        Returns:
            {
                'success': bool,
                'data': {
                    'comments': [...],
                    'total': int,
                    'has_more': bool
                }
            }
        """
        params = {
            'feed_id': feed_id,
            'page': page,
            'page_size': page_size,
            'sort': sort,
        }
        
        resp = self._http_request('GET', '/comments/list', params=params)
        
        if 'data' in resp and 'comments' in resp['data']:
            return {
                'success': True,
                'data': {
                    'comments': [self._parse_comment(c) for c in resp['data']['comments']],
                    'total': resp['data'].get('total', 0),
                    'has_more': resp['data'].get('has_more', False)
                }
            }
        
        return resp
    
    def _parse_comment(self, comment: Dict) -> Dict:
        """解析评论信息"""
        return {
            'id': comment.get('id'),
            'user': comment.get('user', {}),
            'content': comment.get('content'),
            'like_count': comment.get('interact_info', {}).get('like_count', 0),
            'create_time': comment.get('create_time'),
            'replied': False,  # 默认未回复
        }
    
    def reply_comment(self, feed_id: str, comment_id: str, content: str) -> Dict[str, Any]:
        """
        回复评论
        
        Args:
            feed_id: 笔记 ID
            comment_id: 评论 ID
            content: 回复内容
        
        Returns:
            {
                'success': bool,
                'data': {
                    'reply_id': str
                }
            }
        """
        payload = {
            'feed_id': feed_id,
            'comment_id': comment_id,
            'content': content,
        }
        
        resp = self._http_request('POST', '/comments/reply', data=payload)
        
        if 'data' in resp and 'reply_id' in resp['data']:
            return {
                'success': True,
                'data': {'reply_id': resp['data']['reply_id']}
            }
        
        return resp
    
    # ─────────────────────────────────────────
    # 用户数据 API
    # ─────────────────────────────────────────
    
    def get_user_feed(self, user_id: str = None, page: int = 1, 
                     page_size: int = 20) -> Dict[str, Any]:
        """获取用户笔记列表"""
        user_id = user_id or self.user_id
        
        params = {
            'user_id': user_id,
            'page': page,
            'page_size': page_size,
        }
        
        resp = self._http_request('GET', '/user/feeds', params=params)
        
        if 'data' in resp and 'feeds' in resp['data']:
            return {
                'success': True,
                'data': {
                    'feeds': [self._parse_feed(f) for f in resp['data']['feeds']],
                    'total': resp['data'].get('total', 0),
                }
            }
        
        return resp
    
    def get_user_info(self, user_id: str = None) -> Dict[str, Any]:
        """获取用户信息"""
        user_id = user_id or self.user_id
        
        params = {'user_id': user_id}
        resp = self._http_request('GET', '/user/info', params=params)
        
        if 'data' in resp:
            return {
                'success': True,
                'data': resp['data']
            }
        
        return resp
    
    # ─────────────────────────────────────────
    # 数据分析 API
    # ─────────────────────────────────────────
    
    def get_feed_data(self, feed_id: str) -> Dict[str, Any]:
        """
        获取笔记数据统计
        
        Returns:
            {
                'success': bool,
                'data': {
                    'view_count': int,
                    'like_count': int,
                    'comment_count': int,
                    'share_count': int,
                    'collect_count': int
                }
            }
        """
        params = {'feed_id': feed_id}
        resp = self._http_request('GET', '/feeds/data', params=params)
        
        if 'data' in resp:
            return {
                'success': True,
                'data': {
                    'view_count': resp['data'].get('view_count', 0),
                    'like_count': resp['data'].get('like_count', 0),
                    'comment_count': resp['data'].get('comment_count', 0),
                    'share_count': resp['data'].get('share_count', 0),
                    'collect_count': resp['data'].get('collect_count', 0),
                }
            }
        
        return resp


class XHSMockClient:
    """小红书 Mock 客户端（用于测试和演示）"""
    
    def __init__(self, user_id: str = None):
        self.user_id = user_id or "mock_user"
    
    def search_feeds(self, keyword: str, **kwargs) -> Dict[str, Any]:
        """模拟搜索结果"""
        return {
            'success': True,
            'data': {
                'feeds': [
                    {
                        'id': f'feed_{i}',
                        'title': f'{keyword} 热点 {i+1}',
                        'desc': f'关于 {keyword} 的热门内容',
                        'type': '图文',
                        'interact_info': {
                            'like_count': 1000 + i * 100,
                            'comment_count': 50 + i * 10,
                            'share_count': 20 + i * 5,
                        },
                        'user': {'id': 'user_1', 'nickname': '博主'},
                        'image_list': ['https://via.placeholder.com/400'],
                    }
                    for i in range(5)
                ],
                'total': 100,
                'has_more': True
            }
        }
    
    def publish_note(self, title: str, content: str, **kwargs) -> Dict[str, Any]:
        """模拟发布笔记"""
        return {
            'success': True,
            'data': {
                'note_id': f"note_{int(time.time())}",
                'note_url': f"https://xiaohongshu.com/explore/note_{int(time.time())}"
            }
        }
    
    def get_feed_comments(self, feed_id: str, **kwargs) -> Dict[str, Any]:
        """模拟获取评论"""
        return {
            'success': True,
            'data': {
                'comments': [
                    {
                        'id': f'comment_{i}',
                        'user': {'id': f'user_{i}', 'nickname': f'用户{i}'},
                        'content': f'很赞！{i}',
                        'like_count': 10 + i * 5,
                        'create_time': int(time.time()),
                        'replied': False,
                    }
                    for i in range(5)
                ],
                'total': 20,
                'has_more': True
            }
        }
