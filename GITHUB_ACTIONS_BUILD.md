# GitHub Actions 自动编译 APK 指南

## 📋 概述

你已经设置了 GitHub Actions 工作流，现在每次 push 代码到 `main` 分支时，GitHub 会自动编译 Android APK。

## ✅ 工作流配置

工作流文件位置：`.github/workflows/build-apk.yml`

### 触发条件

1. **自动触发**：每次 push 到 `main` 分支
2. **手动触发**：在 GitHub Actions 页面手动触发编译

## 🚀 使用方式

### 方式 1：自动编译（推荐）

只需要像平常一样 commit 和 push：

```bash
cd /Users/bytedance/WorkBuddy/20260316183744/xhs_android

# 修改代码
# ...

# commit 和 push（会自动触发编译）
git add .
git commit -m "feature: 新功能描述"
git push origin main
```

**GitHub 会自动开始编译，约需 20-30 分钟。**

### 方式 2：手动触发编译

如果你想在不 push 的情况下重新编译：

1. 打开 GitHub 仓库页面：https://github.com/lius1ucky/xhs-toolbox
2. 点击 "Actions" 标签
3. 左侧选择 "Build Android APK"
4. 点击 "Run workflow" → "Run workflow"

GitHub 会立即开始编译。

## 📦 下载 APK

编译完成后（约 20-30 分钟），你可以从两个地方下载 APK：

### 方式 1：从 Release 页面下载（推荐）

1. 打开 https://github.com/lius1ucky/xhs-toolbox/releases
2. 最新的 Release 会显示 `v2.0.0-XXX`（XXX 是编译编号）
3. 下载 `xhstoolbox-2.0.0-debug.apk`

### 方式 2：从 Artifacts 下载

1. 打开 GitHub Actions 页面：https://github.com/lius1ucky/xhs-toolbox/actions
2. 点击最新的 "Build Android APK" 工作流
3. 在页面下方找到 "Artifacts" 部分
4. 下载 `xhstoolbox-apk`（ZIP 文件）

## 🔍 查看编译过程

1. 打开 GitHub 仓库：https://github.com/lius1ucky/xhs-toolbox
2. 点击 "Actions" 标签
3. 选择最新的工作流运行
4. 点击 "build" 查看详细的编译日志

## ⚠️ 编译失败怎么办

如果编译失败，你可以：

1. 查看编译日志找出错误原因
2. 修改代码后重新 push（或手动触发）
3. 如果需要帮助，复制错误日志告诉我

常见错误：
- **内存不足**：GitHub Actions 有足够资源，一般不会有这个问题
- **依赖缺失**：检查 `buildozer.spec` 的 `requirements` 是否正确
- **代码语法错误**：修改代码后重新 push

## 📱 安装 APK 到手机

下载完 APK 后，按照以下步骤安装：

```bash
# 1. 确保手机连接并启用 USB 调试
adb devices

# 2. 安装 APK
adb uninstall com.xhs.toolbox  # 先卸载旧版本
adb install -r /path/to/xhstoolbox-2.0.0-debug.apk

# 3. 查看日志
adb logcat | grep -i "xhs\|backend"
```

## 🔑 关键文件

- `.github/workflows/build-apk.yml` - GitHub Actions 工作流配置
- `buildozer.spec` - buildozer 配置文件
- `requirements.txt`（如果有）- Python 依赖

## 📊 工作流步骤

GitHub Actions 会按以下步骤编译：

1. ✅ 检查代码（Checkout）
2. ✅ 安装 Python、Java
3. ✅ 安装 buildozer 和依赖
4. ✅ 下载 Android SDK 和 NDK（约 2GB，只第一次）
5. ✅ 配置 buildozer
6. ✅ **编译 APK**（耗时最长）
7. ✅ 上传 APK 到 GitHub
8. ✅ 创建 Release 并上传 APK

## 💡 优势

✅ **自动化**：无需本地安装 Android SDK、NDK、buildozer
✅ **一致性**：所有编译都在相同的环境（Ubuntu）进行
✅ **版本管理**：自动生成 Release，方便下载管理
✅ **节省空间**：不需要在本地安装 SDK（约 30GB）
✅ **快速**：GitHub 的服务器比本地快

## 🚀 快速开始

```bash
# 1. 修改代码
cd /Users/bytedance/WorkBuddy/20260316183744/xhs_android
# 编辑文件...

# 2. 提交和推送
git add .
git commit -m "feat: 你的功能描述"
git push origin main

# 3. 等待 20-30 分钟
# GitHub Actions 会自动编译 APK

# 4. 下载 APK
# 打开 https://github.com/lius1ucky/xhs-toolbox/releases
# 下载最新版本的 APK

# 5. 安装到手机
adb install -r ~/Downloads/xhstoolbox-2.0.0-debug.apk
```

## 📝 注意事项

1. **第一次编译会比较慢**（20-30 分钟）：因为需要下载 SDK 和 NDK
2. **后续编译会更快**（10-15 分钟）：因为 SDK 已经缓存
3. **每次提交都会触发编译**：如果你频繁 push，会有多个 Release
4. **GitHub 有 Actions 使用限制**：免费账户每月有一定的使用额度

---

**现在你可以开始使用 GitHub Actions 自动编译 APK 了！** 🎉

有任何问题，查看编译日志或联系我。
