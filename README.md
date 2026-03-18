# 小红书运营工具箱 (xhs)

一个基于 Python + Kivy 的小红书运营工具箱，支持搜索热点、自动发布笔记、获取评论等功能。

## 功能特点

- 🔍 **搜索热点** - 搜索小红书热门内容
- 📝 **自动发布** - 自动发布预设的笔记内容
- 💬 **评论管理** - 获取和查看笔记评论
- ⚙️ **灵活配置** - 自定义关键词、发布时间等

## 环境要求

- Python 3.8+
- Kivy 2.2+
- Buildozer (用于打包 Android APK)

## 安装依赖

```bash
pip install kivy==2.2.1 pillow flask werkzeug apscheduler requests
```

## 运行项目

### 桌面端运行

```bash
python main.py
```

或使用专用桌面启动脚本：

```bash
python run_desktop.py
```

### Android APK 打包

#### 使用 Buildozer

1. 安装 Buildozer：
```bash
pip install buildozer
```

2. 初始化 Buildozer：
```bash
buildozer init
```

3. 打包 APK：
```bash
buildozer android debug
```

#### 使用打包脚本

```bash
python build_apk.py
```

或使用 Docker：
```bash
./docker_build.sh
```

## 项目结构

```
xhs/
├── main.py              # 主入口
├── run_desktop.py       # 桌面端启动脚本
├── build_apk.py         # APK 打包脚本
├── buildozer.spec       # Buildozer 配置
├── xhs.kv               # Kivy UI 布局
├── core/                # 核心模块
│   ├── config.py        # 配置管理
│   ├── tasks.py         # 任务逻辑
│   ├── mcp_client.py    # API 客户端
│   ├── local_backend.py # 本地后端服务
│   ├── db.py            # 数据库管理
│   ├── scheduler.py     # 定时任务
│   ├── xhs_api.py       # 小红书 API
│   └── wechat_api.py    # 微信 API
└── assets/              # 资源文件
    ├── posts/           # 帖子内容
    └── fonts/           # 字体文件
```

## 配置说明

配置文件 `settings.json` 包含以下选项：

- `hotspot_keywords` - 热点搜索关键词
- `hotspot_sort_by` - 排序方式（最多点赞/最新发布）
- `publish_count` - 每次发布数量
- `publish_interval_seconds` - 发布间隔秒数
- `publish_scheduled_time` - 定时发布时间
- `comment_check_time` - 评论检查时间
- `active_platform` - 活跃平台 (xhs/wechat)

## 许可证

MIT License

## 作者

lius1ucky
