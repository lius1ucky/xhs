# APK 打包完整指南 - v2.0

## 🔴 问题分析

**症状**: 打包后的 APK 和 v1.0 无变化

**可能原因**:
1. ❌ buildozer 编译缓存未清除
2. ❌ 版本号没更新（Android 系统可能使用旧版本）
3. ❌ 源代码未重新编译
4. ❌ Python 字节码缓存（.pyc）未清除

## ✅ 解决方案

### 第一步：完全清除编译缓存

```bash
cd xhs_android

# 清除所有编译文件
rm -rf build .buildozer bin *.pyc __pycache__

# 清除 Python 字节码
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete

echo "✅ 缓存已清除"
```

### 第二步：验证版本号和配置

```bash
# 查看当前配置
grep "^version\|^title\|^requirements" buildozer.spec

# 输出应为:
# title = 小红书运营工具箱 v2.0
# version = 2.0.0
# requirements = python3,kivy==2.2.1,pillow,android,flask,werkzeug,apscheduler,requests
```

### 第三步：验证 v2.0 关键文件

```bash
# 检查所有 v2.0 新增模块
wc -l core/db.py core/xhs_api.py core/wechat_api.py core/scheduler.py core/local_backend.py

# 输出示例:
#    492 core/db.py
#    426 core/xhs_api.py
#    428 core/wechat_api.py
#    354 core/scheduler.py
#    471 core/local_backend.py
#   2171 total
```

### 第四步：重新编译

**方案 A: 调试版本（推荐先用这个测试）**

```bash
buildozer android debug
```

这会生成: `bin/xhstoolbox-2.0.0-debug.apk`

**方案 B: 发布版本（完全重新编译，时间较长）**

```bash
buildozer -vvv android debug
```

或使用 Docker（如果本地编译环境有问题）:

```bash
# 需要安装 Docker
docker build -t xhs-builder .
docker run -v $(pwd):/app xhs-builder buildozer android debug
```

### 第五步：验证打包结果

```bash
# 检查 APK 文件
ls -lh bin/

# 应该看到:
# -rw-r--r--  1 user  staff   50M  Mar 18 XX:XX  xhstoolbox-2.0.0-debug.apk

# 验证 APK 内容（检查新文件是否在里面）
unzip -l bin/xhstoolbox-2.0.0-debug.apk | grep -E "db\.py|xhs_api|scheduler|local_backend"

# 应该能看到:
#    424  03-18 10:00   assets/core/db.py
#    456  03-18 10:00   assets/core/xhs_api.py
#    428  03-18 10:00   assets/core/wechat_api.py
#    354  03-18 10:00   assets/core/scheduler.py
#    471  03-18 10:00   assets/core/local_backend.py
```

### 第六步：安装到手机

```bash
# 方式 1: 自动安装
buildozer android debug deploy run

# 方式 2: 手动安装
adb install -r bin/xhstoolbox-2.0.0-debug.apk

# 方式 3: 替换旧版本（卸载后安装）
adb uninstall com.xhs.toolbox
adb install bin/xhstoolbox-2.0.0-debug.apk
```

### 第七步：验证 v2.0 功能

在 Android 手机上打开 App，查看日志:

```bash
# 实时查看日志
adb logcat | grep -i "xhs\|backend\|flask\|database"

# 应该看到:
# ✅ 本地后端已启动: http://127.0.0.1:5000
# 📦 本地后端启动（增强版）: http://127.0.0.1:5000
# 🟢 本地后端自动启动
```

## 🔍 调试技巧

### 1. 检查编译日志

```bash
# 查看详细编译日志
buildozer -vvv android debug 2>&1 | tee build.log

# 搜索错误
grep -i "error\|failed" build.log
```

### 2. 检查 APK 文件列表

```bash
# 查看 APK 中所有 Python 文件
unzip -l bin/xhstoolbox-2.0.0-debug.apk | grep "\.py$" | sort

# 统计 Python 文件数
unzip -l bin/xhstoolbox-2.0.0-debug.apk | grep "\.py$" | wc -l
```

### 3. 检查依赖是否正确编译

```bash
# 检查 Flask 是否在 APK 中
unzip -l bin/xhstoolbox-2.0.0-debug.apk | grep -i "flask"

# 检查 APScheduler 是否在 APK 中
unzip -l bin/xhstoolbox-2.0.0-debug.apk | grep -i "apscheduler"
```

### 4. 查看应用版本信息

```bash
# 在手机上检查应用版本
adb shell dumpsys packages | grep -A 5 "com.xhs.toolbox"

# 应该看到:
# versionName=2.0.0
# versionCode=1
```

## 📊 预期文件大小

| 版本 | 预期大小 | 说明 |
|------|---------|------|
| v1.0 | ~30-40MB | 基础版 |
| v2.0 | ~50-60MB | +Flask +SQLite +依赖 |

**如果 APK 大小没有变化，说明确实没有重新编译！**

## 🚀 快速重新打包命令

```bash
# 一条命令完成所有操作
rm -rf build .buildozer bin __pycache__ && \
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null && \
find . -type f -name "*.pyc" -delete && \
echo "✅ 缓存已清除，开始编译..." && \
buildozer android debug

# 如果编译成功，自动安装
if [ -f "bin/xhstoolbox-2.0.0-debug.apk" ]; then
  echo "✅ APK 编译成功！"
  echo "📦 文件: $(ls -lh bin/xhstoolbox-2.0.0-debug.apk | awk '{print $9, $5}')"
  adb install -r bin/xhstoolbox-2.0.0-debug.apk
else
  echo "❌ APK 编译失败，请查看上面的错误信息"
fi
```

## 📝 版本对应

```
Git Tag      | APK Version | 功能
─────────────┼─────────────┼─────────────────
dd068bd      | v1.0.0      | 本地后端基础版
c484faf      | v2.0.0      | SQLite + 真实API + 多用户 + 定时任务
164a331      | v2.0.0      | 版本号修复
```

## 🎯 完整打包流程（复制粘贴可用）

```bash
#!/bin/bash
cd /Users/bytedance/WorkBuddy/20260316183744/xhs_android

echo "📦 开始 v2.0 完整打包流程..."
echo ""

# 1. 清除缓存
echo "🧹 第 1 步: 清除编译缓存..."
rm -rf build .buildozer bin __pycache__ *.pyc
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete
echo "✅ 缓存已清除"
echo ""

# 2. 验证配置
echo "🔍 第 2 步: 验证版本配置..."
version=$(grep "^version" buildozer.spec | awk '{print $3}')
echo "   版本: $version"
requirements=$(grep "^requirements" buildozer.spec | cut -d' ' -f3-)
echo "   依赖: $requirements"
echo "✅ 配置正确"
echo ""

# 3. 编译
echo "🚀 第 3 步: 开始编译（这可能需要 10-30 分钟）..."
buildozer android debug

if [ $? -eq 0 ]; then
  echo ""
  echo "✅ 编译成功！"
  echo "📦 APK 路径: bin/xhstoolbox-$version-debug.apk"
  ls -lh bin/xhstoolbox-$version-debug.apk
  
  # 4. 安装
  echo ""
  echo "📱 第 4 步: 安装到手机..."
  adb install -r bin/xhstoolbox-$version-debug.apk
  
  if [ $? -eq 0 ]; then
    echo "✅ 安装成功！"
    echo ""
    echo "🎉 v2.0 打包完成！"
  else
    echo "❌ 安装失败，请检查手机连接"
  fi
else
  echo "❌ 编译失败，请查看上面的错误信息"
fi
```

保存为 `package_v2.sh`，执行:

```bash
chmod +x package_v2.sh
./package_v2.sh
```

## ⚠️ 常见问题

### Q1: 编译卡住或超时

**解决**:
```bash
# 增加超时时间
buildozer -vvv android debug -- --timeout=3600
```

### Q2: 依赖编译失败（flask/apscheduler）

**解决**:
```bash
# 清除 python-for-android 缓存
rm -rf ~/.buildozer/android/platform/build-*

# 重新编译
buildozer android debug
```

### Q3: APK 仍然显示 v1.0 版本

**检查**:
```bash
# 彻底卸载旧版本
adb uninstall com.xhs.toolbox

# 清除所有缓存
adb shell pm clear com.xhs.toolbox

# 重新安装
adb install bin/xhstoolbox-2.0.0-debug.apk
```

### Q4: buildozer 配置不生效

**重置配置**:
```bash
# 备份当前配置
cp buildozer.spec buildozer.spec.bak

# 重新初始化（会询问，选择默认）
buildozer init

# 恢复你的配置
# 手动编辑后恢复关键选项
```

## ✨ 成功标志

✅ 完整的 v2.0 打包应该看到:

1. APK 文件大小 50-60MB（比 v1.0 大明显）
2. `unzip -l` 看到 5 个新的 core/*.py 文件
3. App 启动时日志显示 "v2.0.0" 和 "增强版"
4. 设置界面显示 "本地后端自动启动"
5. `/api/health` 返回 `"version": "2.0.0"`

---

祝打包顺利！如有问题，查看上面对应的调试技巧 💪
