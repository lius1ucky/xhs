#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_apk.py — 一键打包 APK 脚本
支持 macOS / Linux（buildozer 不支持 Windows 原生，Windows 需用 WSL）

使用方式：
    python build_apk.py          # 调试版 APK
    python build_apk.py release  # 发布版 APK
"""

import subprocess
import sys
import os
import platform
import shutil

ROOT = os.path.dirname(os.path.abspath(__file__))


def check_buildozer():
    if shutil.which("buildozer"):
        return True
    print("❌ 未找到 buildozer，正在尝试安装...")
    ok = subprocess.run(
        [sys.executable, "-m", "pip", "install", "buildozer"],
        capture_output=False
    ).returncode == 0
    if not ok:
        print("\n请手动安装 buildozer：")
        print("  pip install buildozer")
        print("  或参考: https://buildozer.readthedocs.io/en/latest/installation.html")
        return False
    return True


def check_java():
    if shutil.which("java"):
        print("✅ Java 已安装")
        return True
    print("⚠️  未检测到 Java，Android 打包需要 JDK 17+")
    print("   macOS:  brew install openjdk@17")
    print("   Ubuntu: sudo apt install openjdk-17-jdk")
    return False


def check_font():
    font_dir = os.path.join(ROOT, "assets", "fonts")
    os.makedirs(font_dir, exist_ok=True)
    fonts = [f for f in os.listdir(font_dir) if f.endswith((".ttc", ".ttf", ".otf"))]
    if fonts:
        print(f"✅ 已找到字体文件: {fonts[0]}")
        return True
    else:
        print("⚠️  assets/fonts/ 中没有中文字体文件")
        print("   建议放置一个中文字体（如 NotoSansCJK-Regular.ttc）")
        print("   下载地址: https://github.com/googlefonts/noto-cjk/releases")
        print("   文件改名为 font.ttf 放入 assets/fonts/")
        return False


def build(mode="debug"):
    print(f"\n🔨 开始打包 APK（{mode} 模式）...")
    print(f"   项目目录: {ROOT}")

    # 切换到项目目录
    os.chdir(ROOT)

    cmd = ["buildozer", "android", mode]
    result = subprocess.run(cmd)

    if result.returncode == 0:
        # 找生成的 APK 文件
        bin_dir = os.path.join(ROOT, "bin")
        apks = [f for f in os.listdir(bin_dir) if f.endswith(".apk")] if os.path.exists(bin_dir) else []
        print("\n" + "="*50)
        print("✅ 打包成功！")
        if apks:
            for apk in apks:
                print(f"   APK 文件: {os.path.join(bin_dir, apk)}")
        print("="*50)
    else:
        print("\n❌ 打包失败，请查看上方错误日志")
        print("\n常见问题：")
        print("  1. 未安装 JDK 17+  →  brew install openjdk@17")
        print("  2. 未安装 Android SDK  →  buildozer 会自动下载，需联网")
        print("  3. Windows 用户请在 WSL 中运行此脚本")


def main():
    print("="*50)
    print("  📱 小红书运营工具箱 APK 打包")
    print("="*50)
    print()

    mode = "release" if len(sys.argv) > 1 and sys.argv[1] == "release" else "debug"

    # 系统检查
    system = platform.system()
    if system == "Windows":
        print("⚠️  buildozer 不支持 Windows 原生环境")
        print("   请使用 WSL (Windows Subsystem for Linux) 运行此脚本")
        print("   WSL 安装: wsl --install")
        sys.exit(1)

    print("📋 环境检查...")
    has_buildozer = check_buildozer()
    has_java      = check_java()
    check_font()

    if not has_buildozer:
        sys.exit(1)

    if not has_java:
        answer = input("\n⚠️  Java 未安装，继续可能失败。是否继续？[y/N]: ").strip().lower()
        if answer != "y":
            sys.exit(0)

    print()
    build(mode)


if __name__ == "__main__":
    main()
