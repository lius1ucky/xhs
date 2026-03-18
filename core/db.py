#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
db.py — SQLite 数据库管理层
支持多用户、发布记录、凭证管理
"""

import sqlite3
import os
import json
from datetime import datetime
from typing import Optional, List, Dict, Any

# 数据库文件路径（Android 下会被改写）
_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data.db")


class Database:
    """SQLite 数据库管理器"""
    
    def __init__(self, db_path=None):
        if db_path is None:
            db_path = _DB_PATH
        self.db_path = db_path
        self._init_db()
    
    def _get_conn(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_db(self):
        """初始化数据库表"""
        conn = self._get_conn()
        cursor = conn.cursor()
        
        # 用户表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                username TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 凭证表（支持多平台）
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS credentials (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                platform TEXT NOT NULL,
                cred_key TEXT NOT NULL,
                cred_value TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                UNIQUE(user_id, platform, cred_key)
            )
        ''')
        
        # 发布记录表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS publish_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                platform TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT,
                images TEXT,
                tags TEXT,
                post_id TEXT,
                status TEXT DEFAULT 'pending',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                published_at DATETIME,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        # 评论表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                post_id TEXT NOT NULL,
                platform TEXT NOT NULL,
                comment_id TEXT,
                author TEXT,
                content TEXT,
                likes INTEGER DEFAULT 0,
                replied BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                fetched_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')
        
        # 配置表（用户级配置）
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                config_key TEXT NOT NULL,
                config_value TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                UNIQUE(user_id, config_key)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    # ─────────────────────────────────────────
    # 用户管理
    # ─────────────────────────────────────────
    
    def create_user(self, user_id: str, username: str) -> bool:
        """创建用户"""
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO users (user_id, username) VALUES (?, ?)',
                (user_id, username)
            )
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def get_user(self, user_id: str) -> Optional[Dict]:
        """获取用户信息"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    def list_users(self) -> List[Dict]:
        """列出所有用户"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users ORDER BY created_at DESC')
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    # ─────────────────────────────────────────
    # 凭证管理
    # ─────────────────────────────────────────
    
    def set_credential(self, user_id: str, platform: str, cred_key: str, cred_value: str) -> bool:
        """保存平台凭证"""
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO credentials 
                (user_id, platform, cred_key, cred_value, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
            ''', (user_id, platform, cred_key, cred_value))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"保存凭证失败: {e}")
            return False
    
    def get_credential(self, user_id: str, platform: str, cred_key: str) -> Optional[str]:
        """获取平台凭证"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT cred_value FROM credentials WHERE user_id = ? AND platform = ? AND cred_key = ?',
            (user_id, platform, cred_key)
        )
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else None
    
    def get_credentials(self, user_id: str, platform: str) -> Dict[str, str]:
        """获取用户在某平台的所有凭证"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT cred_key, cred_value FROM credentials WHERE user_id = ? AND platform = ?',
            (user_id, platform)
        )
        rows = cursor.fetchall()
        conn.close()
        return {row[0]: row[1] for row in rows}
    
    # ─────────────────────────────────────────
    # 发布记录管理
    # ─────────────────────────────────────────
    
    def add_publish_record(self, user_id: str, platform: str, title: str, 
                          content: str, images: List[str] = None, 
                          tags: List[str] = None, post_id: str = None) -> int:
        """添加发布记录"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO publish_records 
            (user_id, platform, title, content, images, tags, post_id, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id, platform, title, content,
            json.dumps(images or []),
            json.dumps(tags or []),
            post_id,
            'success' if post_id else 'pending'
        ))
        record_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return record_id
    
    def get_publish_record(self, user_id: str, record_id: int) -> Optional[Dict]:
        """获取发布记录"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT * FROM publish_records WHERE id = ? AND user_id = ?',
            (record_id, user_id)
        )
        row = cursor.fetchone()
        conn.close()
        
        if row:
            record = dict(row)
            record['images'] = json.loads(record['images']) if record['images'] else []
            record['tags'] = json.loads(record['tags']) if record['tags'] else []
            return record
        return None
    
    def list_publish_records(self, user_id: str, platform: str = None, limit: int = 100) -> List[Dict]:
        """列出发布记录"""
        conn = self._get_conn()
        cursor = conn.cursor()
        
        if platform:
            cursor.execute('''
                SELECT * FROM publish_records 
                WHERE user_id = ? AND platform = ?
                ORDER BY created_at DESC
                LIMIT ?
            ''', (user_id, platform, limit))
        else:
            cursor.execute('''
                SELECT * FROM publish_records 
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            ''', (user_id, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        records = []
        for row in rows:
            record = dict(row)
            record['images'] = json.loads(record['images']) if record['images'] else []
            record['tags'] = json.loads(record['tags']) if record['tags'] else []
            records.append(record)
        
        return records
    
    def update_publish_record(self, user_id: str, record_id: int, 
                            post_id: str = None, status: str = None) -> bool:
        """更新发布记录"""
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            
            if post_id:
                cursor.execute('''
                    UPDATE publish_records 
                    SET post_id = ?, status = ?, published_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ? AND user_id = ?
                ''', (post_id, status or 'success', record_id, user_id))
            elif status:
                cursor.execute('''
                    UPDATE publish_records 
                    SET status = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ? AND user_id = ?
                ''', (status, record_id, user_id))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"更新记录失败: {e}")
            return False
    
    # ─────────────────────────────────────────
    # 评论管理
    # ─────────────────────────────────────────
    
    def add_comment(self, user_id: str, post_id: str, platform: str, 
                   comment_id: str, author: str, content: str) -> int:
        """添加评论"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO comments 
            (user_id, post_id, platform, comment_id, author, content)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, post_id, platform, comment_id, author, content))
        comment_pk_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return comment_pk_id
    
    def get_comments(self, user_id: str, post_id: str, platform: str = None) -> List[Dict]:
        """获取评论"""
        conn = self._get_conn()
        cursor = conn.cursor()
        
        if platform:
            cursor.execute('''
                SELECT * FROM comments 
                WHERE user_id = ? AND post_id = ? AND platform = ?
                ORDER BY created_at DESC
            ''', (user_id, post_id, platform))
        else:
            cursor.execute('''
                SELECT * FROM comments 
                WHERE user_id = ? AND post_id = ?
                ORDER BY created_at DESC
            ''', (user_id, post_id))
        
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def mark_comment_replied(self, user_id: str, comment_id: int) -> bool:
        """标记评论已回复"""
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE comments SET replied = 1 WHERE id = ? AND user_id = ?',
                (comment_id, user_id)
            )
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"标记评论失败: {e}")
            return False
    
    # ─────────────────────────────────────────
    # 用户配置管理
    # ─────────────────────────────────────────
    
    def set_user_config(self, user_id: str, key: str, value: Any) -> bool:
        """保存用户配置"""
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO user_configs 
                (user_id, config_key, config_value, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            ''', (user_id, key, json.dumps(value)))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"保存配置失败: {e}")
            return False
    
    def get_user_config(self, user_id: str, key: str, default: Any = None) -> Any:
        """获取用户配置"""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT config_value FROM user_configs WHERE user_id = ? AND config_key = ?',
            (user_id, key)
        )
        row = cursor.fetchone()
        conn.close()
        
        if row:
            try:
                return json.loads(row[0])
            except json.JSONDecodeError:
                return row[0]
        return default
    
    # ─────────────────────────────────────────
    # 数据导出
    # ─────────────────────────────────────────
    
    def export_records_as_json(self, user_id: str, platform: str = None) -> str:
        """导出发布记录为 JSON"""
        records = self.list_publish_records(user_id, platform)
        return json.dumps(records, ensure_ascii=False, indent=2, default=str)
    
    def export_records_as_csv(self, user_id: str, platform: str = None) -> str:
        """导出发布记录为 CSV"""
        import csv
        import io
        
        records = self.list_publish_records(user_id, platform)
        
        output = io.StringIO()
        if records:
            writer = csv.DictWriter(output, fieldnames=records[0].keys())
            writer.writeheader()
            for record in records:
                # 转换复杂字段为字符串
                record_copy = record.copy()
                record_copy['images'] = ','.join(record_copy.get('images', []))
                record_copy['tags'] = ','.join(record_copy.get('tags', []))
                writer.writerow(record_copy)
        
        return output.getvalue()
    
    # ─────────────────────────────────────────
    # 统计
    # ─────────────────────────────────────────
    
    def get_stats(self, user_id: str) -> Dict[str, Any]:
        """获取用户统计数据"""
        conn = self._get_conn()
        cursor = conn.cursor()
        
        # 总发布数
        cursor.execute('SELECT COUNT(*) FROM publish_records WHERE user_id = ?', (user_id,))
        total_publishes = cursor.fetchone()[0]
        
        # 平台分布
        cursor.execute('''
            SELECT platform, COUNT(*) as count 
            FROM publish_records 
            WHERE user_id = ? 
            GROUP BY platform
        ''', (user_id,))
        platform_dist = {row[0]: row[1] for row in cursor.fetchall()}
        
        # 状态分布
        cursor.execute('''
            SELECT status, COUNT(*) as count 
            FROM publish_records 
            WHERE user_id = ? 
            GROUP BY status
        ''', (user_id,))
        status_dist = {row[0]: row[1] for row in cursor.fetchall()}
        
        # 评论总数
        cursor.execute('SELECT COUNT(*) FROM comments WHERE user_id = ?', (user_id,))
        total_comments = cursor.fetchone()[0]
        
        # 已回复评论数
        cursor.execute('SELECT COUNT(*) FROM comments WHERE user_id = ? AND replied = 1', (user_id,))
        replied_comments = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_publishes': total_publishes,
            'platform_distribution': platform_dist,
            'status_distribution': status_dist,
            'total_comments': total_comments,
            'replied_comments': replied_comments,
        }


# 全局数据库实例
_db_instance = None


def get_db(db_path=None) -> Database:
    """获取全局数据库实例"""
    global _db_instance
    if _db_instance is None:
        _db_instance = Database(db_path)
    return _db_instance


def set_db_path(path: str):
    """设置数据库路径（Android 下需要调用）"""
    global _DB_PATH
    _DB_PATH = path
