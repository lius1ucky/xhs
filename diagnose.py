#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
APK 诊断脚本 - 检查所有关键模块是否能正常导入
"""

import sys
import os

# 添加项目路径
ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

print("=" * 60)
print("🔍 小红书工具箱 v2.0 诊断报告")
print("=" * 60)
print()

# 检查 Python 版本
print("📌 Python 环境:")
print(f"   版本: {sys.version}")
print(f"   路径: {sys.executable}")
print()

# 检查关键模块导入
print("📦 模块导入检查:")
print("-" * 60)

modules_to_check = [
    ("core.config", "配置管理"),
    ("core.tasks", "任务管理"),
    ("core.db", "数据库"),
    ("core.xhs_api", "小红书 API"),
    ("core.wechat_api", "微信公众号 API"),
    ("core.scheduler", "定时任务调度"),
    ("core.local_backend", "本地后端"),
    ("core.mcp_client", "MCP 客户端"),
    ("kivy.app", "Kivy 应用"),
    ("flask", "Flask 框架"),
    ("sqlite3", "SQLite 数据库"),
]

failed_modules = []
for module_name, description in modules_to_check:
    try:
        __import__(module_name)
        print(f"✅ {module_name:30} ({description})")
    except ImportError as e:
        print(f"❌ {module_name:30} ({description})")
        print(f"   错误: {e}")
        failed_modules.append((module_name, str(e)))
    except Exception as e:
        print(f"⚠️  {module_name:30} ({description})")
        print(f"   异常: {type(e).__name__}: {e}")
        failed_modules.append((module_name, str(e)))

print()

# 检查关键文件
print("📂 关键文件检查:")
print("-" * 60)

files_to_check = [
    "main.py",
    "xhs.kv",
    "buildozer.spec",
    "core/__init__.py",
    "core/config.py",
    "core/db.py",
    "core/xhs_api.py",
    "core/wechat_api.py",
    "core/scheduler.py",
    "core/local_backend.py",
    "core/mcp_client.py",
]

missing_files = []
for file_path in files_to_check:
    full_path = os.path.join(ROOT, file_path)
    if os.path.exists(full_path):
        size = os.path.getsize(full_path)
        print(f"✅ {file_path:40} ({size:,} 字节)")
    else:
        print(f"❌ {file_path:40} (缺失)")
        missing_files.append(file_path)

print()

# 检查数据库初始化
print("🗄️  数据库初始化检查:")
print("-" * 60)

try:
    from core.db import Database, get_db
    print("✅ 可以导入 Database 和 get_db 函数")
    
    # 尝试创建数据库
    test_db_path = os.path.join(ROOT, "test_db.sqlite")
    db = Database(test_db_path)
    print(f"✅ 数据库可以初始化")
    print(f"   路径: {test_db_path}")
    
    # 清理测试数据库
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
        print("✅ 清理测试数据库")
except Exception as e:
    print(f"❌ 数据库初始化失败: {e}")
    import traceback
    traceback.print_exc()

print()

# 检查 Flask
print("🚀 Flask 后端检查:")
print("-" * 60)

try:
    from flask import Flask
    print("✅ Flask 可以导入")
    
    # 尝试创建 Flask 应用
    test_app = Flask(__name__)
    print("✅ 可以创建 Flask 应用")
    
    @test_app.route('/test')
    def test():
        return {'status': 'ok'}
    
    print("✅ 可以定义路由")
except Exception as e:
    print(f"❌ Flask 检查失败: {e}")
    import traceback
    traceback.print_exc()

print()

# 检查 Kivy
print("🎨 Kivy 检查:")
print("-" * 60)

try:
    from kivy.app import App
    from kivy.uix.boxlayout import BoxLayout
    print("✅ Kivy 可以导入")
    
    # 不启动 App，只检查能否定义
    print("✅ Kivy 主要组件都可以导入")
except Exception as e:
    print(f"❌ Kivy 检查失败: {e}")

print()

# 总结
print("=" * 60)
print("📋 诊断总结")
print("=" * 60)

if not failed_modules and not missing_files:
    print("✅ 所有检查通过！APK 应该可以正常运行。")
else:
    print("⚠️  发现以下问题:")
    if failed_modules:
        print("\n❌ 导入失败的模块:")
        for module, error in failed_modules:
            print(f"   - {module}")
            print(f"     {error}")
    
    if missing_files:
        print("\n❌ 缺失的文件:")
        for file in missing_files:
            print(f"   - {file}")

print()
print("建议:")
print("  1. 如果看到 Flask 导入失败：buildozer.spec 需要包含 flask 依赖")
print("  2. 如果看到模块导入失败：检查相应文件的语法错误")
print("  3. 如果看到缺失文件：检查文件是否被正确打包到 APK 中")
print()
