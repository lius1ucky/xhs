#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
wechat_api.py — 微信公众号 API 集成
基于微信官方 API，支持消息、菜单、用户管理等功能
"""

import json
import time
import hashlib
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime
from typing import Dict, List, Optional, Any


class WechatAPIClient:
    """微信公众号 API 客户端"""
    
    # 微信官方 API 端点
    API_HOST = "https://api.weixin.qq.com"
    
    def __init__(self, app_id: str, app_secret: str, access_token: str = None):
        """
        初始化微信客户端
        
        Args:
            app_id: 微信公众号 App ID
            app_secret: 微信公众号 App Secret
            access_token: 访问 token（可选，自动获取）
        """
        self.app_id = app_id
        self.app_secret = app_secret
        self.access_token = access_token
        self.token_expires_at = 0
    
    def _get_access_token(self) -> str:
        """获取/刷新 access_token"""
        # 如果 token 未过期，直接返回
        if self.access_token and time.time() < self.token_expires_at:
            return self.access_token
        
        # 从微信服务器获取新 token
        url = f"{self.API_HOST}/cgi-bin/token"
        params = {
            'grant_type': 'client_credential',
            'appid': self.app_id,
            'secret': self.app_secret,
        }
        
        query_string = urllib.parse.urlencode(params)
        url += f"?{query_string}"
        
        try:
            with urllib.request.urlopen(url, timeout=10) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                
                if 'access_token' in data:
                    self.access_token = data['access_token']
                    self.token_expires_at = time.time() + data.get('expires_in', 7200) - 60
                    return self.access_token
                else:
                    raise RuntimeError(f"获取 token 失败: {data}")
        except Exception as e:
            raise RuntimeError(f"获取微信 token 失败: {e}")
    
    def _http_request(self, method: str, endpoint: str, params: Dict = None, 
                     data: Dict = None, timeout: int = 30) -> Dict:
        """发送 HTTP 请求到微信 API"""
        token = self._get_access_token()
        url = f"{self.API_HOST}{endpoint}"
        
        if params is None:
            params = {}
        params['access_token'] = token
        
        if method == "GET":
            query_string = urllib.parse.urlencode(params)
            url += f"?{query_string}"
            try:
                with urllib.request.urlopen(url, timeout=timeout) as resp:
                    return json.loads(resp.read().decode('utf-8'))
            except urllib.error.HTTPError as e:
                error_body = e.read().decode('utf-8')
                return {'errcode': e.code, 'errmsg': error_body}
        
        elif method == "POST":
            query_string = urllib.parse.urlencode(params)
            url += f"?{query_string}"
            
            payload = json.dumps(data or {}).encode('utf-8')
            headers = {'Content-Type': 'application/json'}
            
            req = urllib.request.Request(url, data=payload, headers=headers, method=method)
            try:
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    return json.loads(resp.read().decode('utf-8'))
            except urllib.error.HTTPError as e:
                error_body = e.read().decode('utf-8')
                return {'errcode': e.code, 'errmsg': error_body}
    
    # ─────────────────────────────────────────
    # 消息发送 API
    # ─────────────────────────────────────────
    
    def send_text_message(self, openid: str, content: str) -> Dict[str, Any]:
        """
        发送文本消息
        
        Args:
            openid: 用户 openid
            content: 消息内容
        
        Returns:
            {
                'success': bool,
                'data': {
                    'msgid': str
                }
            }
        """
        payload = {
            'touser': openid,
            'msgtype': 'text',
            'text': {'content': content}
        }
        
        resp = self._http_request('POST', '/cgi-bin/message/mass/send', data=payload)
        
        if resp.get('errcode') == 0:
            return {
                'success': True,
                'data': {'msgid': resp.get('msg_id')}
            }
        
        return {
            'success': False,
            'error': resp.get('errmsg', '发送失败')
        }
    
    def send_news_message(self, openid: str, media_id: str) -> Dict[str, Any]:
        """
        发送图文消息
        
        Args:
            openid: 用户 openid
            media_id: 图文消息素材 ID
        
        Returns:
            {
                'success': bool,
                'data': {
                    'msgid': str
                }
            }
        """
        payload = {
            'touser': openid,
            'msgtype': 'mpnews',
            'mpnews': {'media_id': media_id}
        }
        
        resp = self._http_request('POST', '/cgi-bin/message/mass/send', data=payload)
        
        if resp.get('errcode') == 0:
            return {
                'success': True,
                'data': {'msgid': resp.get('msg_id')}
            }
        
        return {
            'success': False,
            'error': resp.get('errmsg', '发送失败')
        }
    
    # ─────────────────────────────────────────
    # 用户管理 API
    # ─────────────────────────────────────────
    
    def get_followers(self, first_user_id: str = None) -> Dict[str, Any]:
        """
        获取粉丝列表
        
        Args:
            first_user_id: 拉取的第一个用户的 OPENID，不填默认从头开始拉取
        
        Returns:
            {
                'success': bool,
                'data': {
                    'total': int,
                    'count': int,
                    'data': {
                        'openid': [...]
                    },
                    'next_openid': str
                }
            }
        """
        params = {}
        if first_user_id:
            params['begin_openid'] = first_user_id
        
        resp = self._http_request('GET', '/cgi-bin/user/get', params=params)
        
        if resp.get('errcode') is None or resp.get('errcode') == 0:
            return {
                'success': True,
                'data': {
                    'total': resp.get('total', 0),
                    'count': resp.get('count', 0),
                    'openids': resp.get('data', {}).get('openid', []),
                    'next_openid': resp.get('next_openid', '')
                }
            }
        
        return {
            'success': False,
            'error': resp.get('errmsg', '获取粉丝列表失败')
        }
    
    def get_user_info(self, openid: str) -> Dict[str, Any]:
        """
        获取用户信息
        
        Args:
            openid: 用户 openid
        
        Returns:
            {
                'success': bool,
                'data': {
                    'openid': str,
                    'nickname': str,
                    'sex': int,  # 1 男 2 女 0 未知
                    'language': str,
                    'city': str,
                    'province': str,
                    'country': str,
                    'headimgurl': str,
                    'subscribe_time': int
                }
            }
        """
        params = {
            'openid': openid,
            'lang': 'zh_CN'
        }
        
        resp = self._http_request('GET', '/cgi-bin/user/info', params=params)
        
        if resp.get('errcode') is None or resp.get('errcode') == 0:
            return {
                'success': True,
                'data': {
                    'openid': resp.get('openid'),
                    'nickname': resp.get('nickname'),
                    'sex': resp.get('sex'),
                    'city': resp.get('city'),
                    'province': resp.get('province'),
                    'country': resp.get('country'),
                    'headimgurl': resp.get('headimgurl'),
                    'subscribe_time': resp.get('subscribe_time'),
                }
            }
        
        return {
            'success': False,
            'error': resp.get('errmsg', '获取用户信息失败')
        }
    
    # ─────────────────────────────────────────
    # 素材管理 API
    # ─────────────────────────────────────────
    
    def upload_news(self, articles: List[Dict]) -> Dict[str, Any]:
        """
        上传图文素材
        
        Args:
            articles: 图文数组
                [{
                    'title': str,
                    'author': str,
                    'digest': str,
                    'show_cover_pic': int,  # 0/1
                    'content': str,
                    'content_source_url': str,
                    'thumb_media_id': str
                }, ...]
        
        Returns:
            {
                'success': bool,
                'data': {
                    'media_id': str,
                    'item_id': int
                }
            }
        """
        payload = {
            'articles': articles
        }
        
        resp = self._http_request('POST', '/cgi-bin/material/add_news', data=payload, timeout=60)
        
        if resp.get('errcode') is None or resp.get('errcode') == 0:
            return {
                'success': True,
                'data': {
                    'media_id': resp.get('media_id'),
                    'item_id': resp.get('item_id')
                }
            }
        
        return {
            'success': False,
            'error': resp.get('errmsg', '上传素材失败')
        }
    
    def get_materials(self, type: str = "news", offset: int = 0, 
                     count: int = 20) -> Dict[str, Any]:
        """
        获取素材列表
        
        Args:
            type: 素材类型 ("image" / "news" / "video" / "voice")
            offset: 从全部素材的该偏移位置开始返回
            count: 返回素材的数量
        
        Returns:
            {
                'success': bool,
                'data': {
                    'total_count': int,
                    'item_count': int,
                    'item': [...]
                }
            }
        """
        payload = {
            'type': type,
            'offset': offset,
            'count': count
        }
        
        resp = self._http_request('POST', '/cgi-bin/material/batchget_material', data=payload)
        
        if resp.get('errcode') is None or resp.get('errcode') == 0:
            return {
                'success': True,
                'data': {
                    'total_count': resp.get('total_count', 0),
                    'item_count': resp.get('item_count', 0),
                    'items': resp.get('item', [])
                }
            }
        
        return {
            'success': False,
            'error': resp.get('errmsg', '获取素材失败')
        }


class WechatMockClient:
    """微信 Mock 客户端（用于测试和演示）"""
    
    def __init__(self, app_id: str = None, app_secret: str = None):
        self.app_id = app_id or "mock_app_id"
        self.app_secret = app_secret or "mock_app_secret"
    
    def send_text_message(self, openid: str, content: str) -> Dict[str, Any]:
        """模拟发送文本消息"""
        return {
            'success': True,
            'data': {'msgid': f"msg_{int(time.time())}"}
        }
    
    def get_followers(self, first_user_id: str = None) -> Dict[str, Any]:
        """模拟获取粉丝列表"""
        return {
            'success': True,
            'data': {
                'total': 100,
                'count': 5,
                'openids': [f'openid_{i}' for i in range(5)],
                'next_openid': 'openid_next'
            }
        }
    
    def get_user_info(self, openid: str) -> Dict[str, Any]:
        """模拟获取用户信息"""
        return {
            'success': True,
            'data': {
                'openid': openid,
                'nickname': f'用户{openid[:5]}',
                'sex': 1,
                'city': '北京',
                'province': '北京',
                'country': '中国',
                'headimgurl': 'https://via.placeholder.com/96',
                'subscribe_time': int(time.time()),
            }
        }
    
    def get_materials(self, type: str = "news", offset: int = 0, 
                     count: int = 20) -> Dict[str, Any]:
        """模拟获取素材列表"""
        return {
            'success': True,
            'data': {
                'total_count': 50,
                'item_count': 5,
                'items': [
                    {
                        'media_id': f'media_{i}',
                        'content': {
                            'title': f'素材 {i}',
                            'author': '作者',
                            'digest': f'摘要 {i}',
                        }
                    }
                    for i in range(5)
                ]
            }
        }
