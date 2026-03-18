[app]
title = 小红书运营工具箱 v2.0
package.name = xhstoolbox
package.domain = com.xhs.toolbox
source.dir = .
source.include_exts = py,png,jpg,kv,json,ttc,ttf,otf,md
source.include_patterns = assets/*,assets/fonts/*,assets/posts/*,core/*.py
source.exclude_dirs = tests, bin, .git, __pycache__, build
version = 2.0.0
requirements = python3,kivy==2.2.1,pillow,android,flask,werkzeug,apscheduler,requests
orientation = portrait
fullscreen = 0
android.minapi = 26
android.ndk = 25b
android.accept_sdk_license = True
android.archs = arm64-v8a, armeabi-v7a

# 权限
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE

# 图标（可替换为自定义图标）
# icon.filename = %(source.dir)s/assets/icon.png

# 启动画面
# presplash.filename = %(source.dir)s/assets/presplash.png
presplash_color = #14141e

# 签名（发布时填写，调试时留空）
# android.release_artifact = aab
# android.keystore = mykey.jks
# android.keystore_passwd = yourpassword
# android.keyalias = mykey
# android.keyalias_passwd = yourpassword

[buildozer]
log_level = 2
warn_on_root = 1
