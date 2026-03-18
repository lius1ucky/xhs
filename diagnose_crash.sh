#!/bin/bash
# diagnose_crash.sh - APK 闪退诊断脚本

set -e

echo "🔍 小红书工具箱 APK 闪退诊断"
echo "=================================="
echo ""

# 检查 adb
if ! command -v adb &> /dev/null; then
    echo "❌ 错误：未找到 adb 命令"
    echo "请安装 Android SDK 或将 adb 加入 PATH"
    exit 1
fi

# 检查设备
echo "📱 检查连接的设备..."
devices=$(adb devices | tail -n +2 | grep -v "^$" | wc -l)

if [ $devices -eq 0 ]; then
    echo "❌ 未找到连接的设备"
    echo "请确保："
    echo "  1. 手机连接到电脑"
    echo "  2. 启用了 USB 调试"
    echo "  3. 在手机上允许了 USB 调试连接"
    exit 1
fi

echo "✅ 找到 $devices 个设备"
echo ""

# 获取包名
PACKAGE="com.xhs.toolbox"
ACTIVITY="XhsApp"

echo "📦 应用信息"
echo "  包名: $PACKAGE"
echo "  Activity: $ACTIVITY"
echo ""

# 卸载旧版本
echo "🔄 卸载旧版本..."
adb uninstall $PACKAGE 2>/dev/null || true
sleep 1

# 提示用户
echo ""
echo "📥 请提供 APK 文件路径"
read -p "APK 文件路径 (或直接按 Enter 查找 bin/ 目录): " apk_path

if [ -z "$apk_path" ]; then
    # 自动查找 APK
    apk_path=$(find bin -name "*.apk" -type f 2>/dev/null | head -1)
    if [ -z "$apk_path" ]; then
        echo "❌ 未找到 APK 文件"
        exit 1
    fi
fi

if [ ! -f "$apk_path" ]; then
    echo "❌ APK 文件不存在: $apk_path"
    exit 1
fi

echo "📦 APK 文件: $apk_path"
echo "📊 文件大小: $(du -h "$apk_path" | cut -f1)"
echo ""

# 安装 APK
echo "🚀 安装 APK..."
adb install -r "$apk_path"
echo "✅ 安装完成"
echo ""

# 清空日志
echo "📝 清空日志..."
adb logcat -c
sleep 1

# 启动应用
echo "⏱️  启动应用..."
adb shell am start -n "$PACKAGE/.$ACTIVITY" 2>/dev/null || adb shell am start -n "$PACKAGE/$PACKAGE.$ACTIVITY" 2>/dev/null
sleep 2

# 收集日志
echo ""
echo "🔍 收集崩溃日志（等待 10 秒，如果 App 立即闪退会显示错误）..."
echo "=================================="
echo ""

# 获取日志
logcat_output=$(adb logcat -d)

# 查找错误信息
echo "$logcat_output" | grep -E "FATAL|Exception|Error" | tail -20

echo ""
echo "=================================="
echo ""
echo "📋 完整日志已保存到 crash_log.txt"
echo "$logcat_output" > crash_log.txt

echo ""
echo "🔍 分析结果："
echo ""

# 检查是否有 Python 错误
if echo "$logcat_output" | grep -q "ImportError\|ModuleNotFoundError"; then
    echo "❌ 发现导入错误"
    echo "$logcat_output" | grep -E "ImportError|ModuleNotFoundError" | head -3
    echo ""
fi

# 检查是否有 Kivy 错误
if echo "$logcat_output" | grep -q "kivy"; then
    echo "❌ 发现 Kivy 相关错误"
    echo "$logcat_output" | grep "kivy" | head -3
    echo ""
fi

# 检查是否有 Flask 错误
if echo "$logcat_output" | grep -q "flask\|Flask"; then
    echo "⚠️  Flask 相关信息"
    echo "$logcat_output" | grep -i "flask" | head -3
    echo ""
fi

echo "💡 下一步："
echo "1. 查看完整日志: cat crash_log.txt"
echo "2. 搜索 'Exception' 或 'Error' 关键词"
echo "3. 如果有具体错误，告诉我错误信息"
echo ""
