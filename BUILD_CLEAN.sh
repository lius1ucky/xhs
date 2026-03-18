#!/bin/bash

# 彻底清除编译缓存和打包
echo "🧹 清除 buildozer 缓存..."
rm -rf build .buildozer bin *.pyc __pycache__

# 清除 Python 缓存
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete

echo "✅ 缓存已清除"

# 验证关键文件存在
echo ""
echo "📦 验证 v2.0 关键文件..."
echo "─────────────────────────"

files=(
  "core/db.py"
  "core/xhs_api.py"
  "core/wechat_api.py"
  "core/scheduler.py"
  "core/local_backend.py"
  "main.py"
  "buildozer.spec"
)

for file in "${files[@]}"; do
  if [ -f "$file" ]; then
    lines=$(wc -l < "$file")
    echo "✅ $file ($lines 行)"
  else
    echo "❌ $file (缺失)"
  fi
done

echo ""
echo "🔍 检查版本号..."
version=$(grep "^version" buildozer.spec | awk '{print $3}')
echo "   buildozer.spec 版本: $version"

title=$(grep "^title" buildozer.spec | sed 's/title = //')
echo "   App 标题: $title"

requirements=$(grep "^requirements" buildozer.spec)
echo "   依赖: $requirements"

echo ""
echo "🚀 准备开始编译 v2.0..."
echo "   执行: buildozer android debug"
echo ""
