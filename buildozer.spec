[app]

title = NDT2 Test

package.name = ndt2test
package.domain = com.industrialradiographyiran

source.dir = .
source.include_exts = py,kv,png,jpg,jpeg,ttf,atlas,txt
source.exclude_dirs = .git,.github,.buildozer,bin,tests

version = 0.2.0

requirements = python3==3.11.5,hostpython3==3.11.5,kivy==2.3.0,arabic-reshaper==3.0.0,python-bidi==0.4.2

icon.filename = %(source.dir)s/icon.png

orientation = portrait
fullscreen = 0

android.api = 33
android.minapi = 23
android.ndk = 25b
android.ndk_api = 23

android.archs = arm64-v8a
android.accept_sdk_license = True
android.debug_artifact = apk

p4a.branch = v2024.01.21

[buildozer]

log_level = 2
warn_on_root = 1
