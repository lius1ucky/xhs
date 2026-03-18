#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mcp_client.py — REST API 通信模块
支持本地后端（自动启动）或远程后端
"""

import json
import urllib.request
import urllib.error
from core import config

# 尝试导入本地后端模块
try:
    from core import local_backend
    HAS_LOCAL_BACKEND = True
except Exception as e:
    print(f"⚠️  无法导入本地后端模块: {e}")
    local_backend = None
    HAS_LOCAL_BACKEND = False

_local_backend_started = False


def _ensure_backend_started():
    """确保本地后端已启动（如果配置为本地模式）"""
    global _local_backend_started
    
    if not HAS_LOCAL_BACKEND or not local_backend or _local_backend_started:
        return
    
    try:
        cfg = config.load()
        backend_mode = cfg.get("backend_mode", "local")
        
        if backend_mode == "local" and HAS_LOCAL_BACKEND:
            try:
                if not local_backend.is_running():
                    result = local_backend.start_backend(host="127.0.0.1", port=5000)
                    if result:
                        _local_backend_started = True
                    else:
                        print("⚠️  后端启动失败")
            except Exception as e:
                print(f"⚠️  启动后端异常: {e}")
    except Exception as e:
        print(f"⚠️  确保后端已启动时异常: {e}")


def _http_request(method, url, payload=None, headers=None, timeout=60):
    """通用 HTTP 请求"""
    # 确保后端已启动
    _ensure_backend_started()
    
    if headers is None:
        headers = {}
    
    headers["Content-Type"] = "application/json"
    
    # 获取配置中的 user_id
    cfg = config.load()
    user_id = cfg.get("user_id", "default_user")
    headers["X-User-Id"] = user_id
    
    data = json.dumps(payload).encode("utf-8") if payload else None
    req = urllib.request.Request(url, data=data, method=method)
    
    for k, v in headers.items():
        req.add_header(k, v)
    
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8")
        raise RuntimeError(f"HTTP {e.code}: {error_body}")
    except Exception as e:
        raise RuntimeError(f"请求失败: {e}")


def _http_post(url, payload, headers=None, timeout=60):
    """POST 请求"""
    return _http_request("POST", url, payload, headers, timeout)


def _http_get(url, headers=None, timeout=60):
    """GET 请求"""
    return _http_request("GET", url, None, headers, timeout)


def search_hotspot(keyword, filters=None):
    """搜索热点"""
    cfg = config.load()
    api_url = cfg.get("api_url", "http://localhost:5000/api")
    
    payload = {
        "keyword": keyword,
        "filters": filters or {}
    }
    
    resp_text = _http_post(f"{api_url}/content/search-hotspot", payload, timeout=60)
    return json.loads(resp_text)


def publish_content(title, content, images=None, tags=None):
    """发布内容"""
    cfg = config.load()
    api_url = cfg.get("api_url", "http://localhost:5000/api")
    
    payload = {
        "title": title,
        "content": content,
        "images": images or [],
        "tags": tags or []
    }
    
    resp_text = _http_post(f"{api_url}/content/publish", payload, timeout=180)
    return json.loads(resp_text)


def get_comments(post_id, platform=None):
    """获取评论"""
    cfg = config.load()
    api_url = cfg.get("api_url", "http://localhost:5000/api")
    
    url = f"{api_url}/content/comments/{post_id}"
    if platform:
        url += f"?platform={platform}"
    
    resp_text = _http_get(url, timeout=60)
    return json.loads(resp_text)


def get_publish_history(platform=None, limit=10):
    """获取发布历史"""
    cfg = config.load()
    api_url = cfg.get("api_url", "http://localhost:5000/api")
    
    url = f"{api_url}/content/history?limit={limit}"
    if platform:
        url += f"&platform={platform}"
    
    resp_text = _http_get(url, timeout=30)
    return json.loads(resp_text)


def call_tool(tool_name, tool_args, timeout=None):
    """调用 MCP 工具（通过 HTTP 请求调用本地后端）"""
    if timeout is None:
        timeout = 180

    cfg = config.load()
    api_url = cfg.get("api_url", "http://127.0.0.1:5000/api")

    # 确保本地后端已启动
    _ensure_backend_started()

    # 映射 MCP 工具名称到 REST API 端点
    if tool_name == "search_feeds":
        payload = {
            "keyword": tool_args.get("keyword", ""),
            "filters": tool_args.get("filters", {})
        }
        resp_text = _http_post(f"{api_url}/content/search-hotspot", payload, timeout=timeout)
        return json.loads(resp_text)

    elif tool_name == "publish_content":
        payload = {
            "title": tool_args.get("title", ""),
            "content": tool_args.get("content", ""),
            "images": tool_args.get("images", []),
            "tags": tool_args.get("tags", [])
        }
        resp_text = _http_post(f"{api_url}/content/publish", payload, timeout=timeout)
        return json.loads(resp_text)

    elif tool_name == "get_feed_detail":
        feed_id = tool_args.get("feed_id", "")
        platform = tool_args.get("platform", "xhs")
        url = f"{api_url}/content/comments/{feed_id}?platform={platform}"
        resp_text = _http_get(url, timeout=timeout)
        return json.loads(resp_text)

    else:
        raise RuntimeError(f"未知的工具: {tool_name}")
