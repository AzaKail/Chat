[app]
# Общие параметры
title = ChatApp
package.name = chatapp
package.domain = org.example
source.main = main.py
source.dir = .
version = 1.0

# Зависимости
requirements = python3,kivy,kivymd,supabase-py,pika

# Android
android.api = 30
android.minapi = 19
android.ndk = 25b
android.sdk = 23
android.permissions = INTERNET
android.gradle_dependencies = com.android.support:support-v4:27.1.1

# Buildozer
p4a.branch = develop
