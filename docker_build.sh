#!/bin/bash
# docker_build.sh — 用 Docker 一键打包 APK（Mac/Linux 通用）
# 前提：已安装 Docker Desktop

set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
echo "📦 项目目录: $PROJECT_DIR"

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo "❌ 未找到 Docker，请先安装 Docker Desktop"
    echo "   下载地址: https://www.docker.com/products/docker-desktop"
    exit 1
fi

if ! docker info &> /dev/null; then
    echo "❌ Docker 未运行，请先启动 Docker Desktop"
    exit 1
fi

echo "🐳 使用 Docker 打包 APK（首次运行会拉取镜像，约 2GB，请耐心等待）..."
echo ""

docker run --rm \
    -v "$PROJECT_DIR":/home/user/hostcwd \
    kivy/buildozer:latest \
    android debug

echo ""
APK_FILE=$(ls "$PROJECT_DIR/bin/"*.apk 2>/dev/null | head -1)
if [ -n "$APK_FILE" ]; then
    echo "✅ 打包成功！"
    echo "   APK 文件: $APK_FILE"
    echo "   文件大小: $(du -h "$APK_FILE" | cut -f1)"
else
    echo "❌ 未找到 APK 文件，请检查上方错误日志"
fi
