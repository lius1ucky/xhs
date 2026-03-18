#!/bin/bash

# 快速 v2.0 打包脚本
# 使用: ./package_v2.sh

set -e  # 任何错误都退出

cd "$(dirname "$0")"

echo "╔════════════════════════════════════════════════╗"
echo "║     小红书工具箱 v2.0 快速打包脚本              ║"
echo "╚════════════════════════════════════════════════╝"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 第一步：清除缓存
echo -e "${YELLOW}🧹 第 1 步: 清除编译缓存...${NC}"
rm -rf build .buildozer bin __pycache__ 2>/dev/null || true
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
echo -e "${GREEN}✅ 缓存已清除${NC}"
echo ""

# 第二步：验证配置
echo -e "${YELLOW}🔍 第 2 步: 验证版本配置...${NC}"

version=$(grep "^version" buildozer.spec | awk '{print $3}')
title=$(grep "^title" buildozer.spec | sed 's/title = //')
requirements=$(grep "^requirements" buildozer.spec | cut -d' ' -f3- | tr ',' '\n' | head -5 | tr '\n' ',' | sed 's/,$//')

echo "   版本号: $version"
echo "   应用名: $title"
echo "   主要依赖: $requirements..."
echo ""

# 验证关键文件
echo -e "${YELLOW}📦 检查 v2.0 关键文件...${NC}"

files=("core/db.py" "core/xhs_api.py" "core/wechat_api.py" "core/scheduler.py" "core/local_backend.py")
all_exist=true

for file in "${files[@]}"; do
  if [ -f "$file" ]; then
    lines=$(wc -l < "$file")
    echo "   ✅ $file ($lines 行)"
  else
    echo "   ❌ $file (缺失)"
    all_exist=false
  fi
done

if [ "$all_exist" = false ]; then
  echo -e "${RED}❌ 某些关键文件缺失，请检查项目结构${NC}"
  exit 1
fi

echo -e "${GREEN}✅ 所有关键文件都已就绪${NC}"
echo ""

# 第三步：编译
echo -e "${YELLOW}🚀 第 3 步: 开始编译（这可能需要 10-30 分钟）...${NC}"
echo "   执行: buildozer android debug"
echo ""

if buildozer android debug; then
  echo ""
  echo -e "${GREEN}✅ 编译成功！${NC}"
  
  # 检查 APK 文件
  if [ -f "bin/xhstoolbox-$version-debug.apk" ]; then
    size=$(ls -lh "bin/xhstoolbox-$version-debug.apk" | awk '{print $5}')
    echo -e "${GREEN}📦 APK 文件: bin/xhstoolbox-$version-debug.apk ($size)${NC}"
    echo ""
    
    # 验证 APK 内容
    echo -e "${YELLOW}🔍 验证 APK 内容...${NC}"
    new_files=$(unzip -l "bin/xhstoolbox-$version-debug.apk" 2>/dev/null | grep -E "db\.py|xhs_api|scheduler|local_backend" | wc -l)
    
    if [ "$new_files" -gt 0 ]; then
      echo -e "${GREEN}✅ APK 包含 v2.0 新文件（$new_files 个）${NC}"
    else
      echo -e "${RED}⚠️  APK 中未找到 v2.0 新文件，可能编译有问题${NC}"
    fi
    
    echo ""
    echo -e "${YELLOW}📱 是否要安装到手机？(y/n)${NC}"
    read -r install_choice
    
    if [ "$install_choice" = "y" ] || [ "$install_choice" = "Y" ]; then
      echo -e "${YELLOW}📱 第 4 步: 安装到手机...${NC}"
      
      if adb install -r "bin/xhstoolbox-$version-debug.apk"; then
        echo -e "${GREEN}✅ 安装成功！${NC}"
        echo ""
        echo -e "${GREEN}🎉 v2.0 打包完成！${NC}"
        echo ""
        echo "   查看日志: adb logcat | grep -i 'xhs\\|backend\\|flask'"
        echo "   手机端: 打开 App，查看设置界面是否显示 v2.0 特性"
      else
        echo -e "${RED}❌ 安装失败，请检查："
        echo "   1. 手机是否正确连接"
        echo "   2. USB 调试是否已启用"
        echo "   3. 执行: adb devices${NC}"
      fi
    else
      echo -e "${YELLOW}⏭️  跳过安装${NC}"
      echo "   手动安装: adb install -r bin/xhstoolbox-$version-debug.apk"
    fi
  else
    echo -e "${RED}❌ APK 文件未找到${NC}"
    exit 1
  fi
else
  echo ""
  echo -e "${RED}❌ 编译失败${NC}"
  echo ""
  echo "可能的原因："
  echo "  1. buildozer 环境未正确配置"
  echo "  2. Java/Android SDK 版本不兼容"
  echo "  3. 依赖库编译失败"
  echo ""
  echo "解决步骤:"
  echo "  1. 查看上面的编译错误日志"
  echo "  2. 尝试完全清除缓存: rm -rf ~/.buildozer"
  echo "  3. 查看 APK_BUILD_GUIDE.md 中的调试部分"
  exit 1
fi
