[app]
# Имя вашего приложения
title = ChatApp

# Пакетное имя
package.name = chatapp
package.domain = org.example

# Главный файл (точка входа)
source.main = main.py

# Исходная директория
source.dir = .

# Значок приложения (укажите путь к иконке, если есть)
# icon.filename = icon.png

# Поддерживаемые форматы APK
android.archs = armeabi-v7a, arm64-v8a

# Текущая версия приложения
version = 1.0

# Список используемых библиотек
requirements = python3,kivy,kivymd,supabase-py,pika

# Минимальная версия Android (API 19 = Android 4.4)
android.minapi = 19

# Разрешения Android
android.permissions = INTERNET

# Язык и раскладка
osx.python_version = 3
osx.kivy_version = 2.1.0

# Buildozer автоматически включает все файлы в исходной директории
# Если нужно что-то исключить:
# exclude_patterns = license,images/*.png,images/original/*

# Точки входа для компиляции
p4a.branch = develop
p4a.bootstrap = sdl2
