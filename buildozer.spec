[app]
title = ИТОГ — подготовка к сочинению
package.name = itogessay
package.domain = org.itogcoach
source.dir = .
source.include_exts = py,kv,png,jpg,json,txt,md,gguf
source.include_patterns = data/*.json,assets/models/*.gguf
source.exclude_dirs = .git,.buildozer,venv,__pycache__,tests,native/build-android
version = 1.0.0
requirements = python3,kivy,pyjnius
orientation = portrait
fullscreen = 0

# APK предназначен для современных ARM64-телефонов, включая Samsung S24 Ultra.
android.api = 35
android.minapi = 28
android.archs = arm64-v8a
android.add_libs_arm64_v8a = native/libs/arm64-v8a/libessay_llama.so
android.allow_backup = False
android.release_artifact = apk
android.debug_artifact = apk

# Приложение не отправляет сочинения и запросы в интернет.
android.permissions =

[buildozer]
log_level = 2
warn_on_root = 1
android.sdk_path = /home/runner/android-sdk 
android.ndk_path = /home/runner/android-sdk/ndk/27.2.12479018 
android.accept_sdk_license = True 
