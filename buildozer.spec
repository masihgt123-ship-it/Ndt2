[app]

title = ndt
package.name = ndtsafedistance
package.domain = com.industrialradiographyiran

source.dir = .
source.include_exts = py,kv,png,jpg,jpeg,webp,atlas,ttf
source.exclude_dirs = .git,.github,__pycache__,bin,.buildozer

version = 1.0

requirements = python3==3.11.5,hostpython3==3.11.5,kivy==2.3.1,arabic-reshaper==3.0.0,python-bidi==0.4.2,six==1.17.0

orientation = portrait
fullscreen = 0

icon.filename = %(source.dir)s/icon.png

# Native startup screen, before Python starts.
# The custom 3-second logo screen is implemented in main.py.
presplash.filename = %(source.dir)s/icon.png
android.presplash_color = #0B1023

android.api = 34
android.minapi = 23
android.ndk = 25b
android.ndk_api = 23
android.accept_sdk_license = True

android.archs = arm64-v8a
android.debug_artifact = apk
android.allow_backup = False
android.logcat_filters = *:S python:D

p4a.branch = v2024.01.21

[buildozer]

log_level = 2
warn_on_root = 1
