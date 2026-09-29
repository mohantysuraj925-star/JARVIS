[app]

title = JARVIS by Suraj
package.name = jarvisbysuraj
package.domain = com.suraj.jarvis
source.dir = .
source.include_exts = py,png,svg,kv
version = 0.1.0
requirements = python3,kivy,websockets,pyjnius
orientation = portrait
fullscreen = 0
icon.filename = %(source.dir)s/icon.png

android.permissions = INTERNET,RECORD_AUDIO
android.api = 35
android.minapi = 23
android.ndk = 27c
android.archs = arm64-v8a
android.accept_sdk_license = True
android.private_storage = True
android.enable_androidx = True

[buildozer]
log_level = 2
warn_on_root = 1
