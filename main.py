from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivymd.app import MDApp
from supabase import create_client, Client
from rabbitmq_chat import RabbitMQChat
from kivymd.uix.boxlayout import MDBoxLayout

import pika
import json
import threading
import time
from datetime import datetime
import logging
import sqlite3


import os
import sys

def get_resource_path(relative_path):
    """Определяет путь к ресурсам в режиме .exe или скрипта."""
    if getattr(sys, 'frozen', False):
        # Если приложение запущено как .exe
        base_path = sys._MEIPASS
    else:
        # Если приложение запускается как обычный скрипт
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Пример: загрузка .kv файлов из папки screens
kv_file_path = get_resource_path("screens/some_file.kv")



# Supabase Configuration
SUPABASE_URL = "https://fywpfnnjxfohwewjsrbo.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZ5d3Bmbm5qeGZvaHdld2pzcmJvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzI5NTI1OTYsImV4cCI6MjA0ODUyODU5Nn0.17WMM-gDxg1ENNNfIq-vNDHNaKBryiXOj31SPSlopCs"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# CLOUDAMQP Configuration
CLOUDAMQP_URL = "amqps://sjmflnbl:9hEj4LOr6cCJL6EsYhBPHgTlFum9ql92@dog-01.lmq.cloudamqp.com/sjmflnbl"
rabbitmq_chat = RabbitMQChat(CLOUDAMQP_URL)


# Функция для сохранения сообщения в базу данных
def save_message_to_db(chat_name, sender, message):
    """Сохраняет сообщение в базу данных."""
    conn = sqlite3.connect("chat_messages.db")
    cursor = conn.cursor()

    # Создайте таблицу, если она не существует
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            chat_name TEXT,
            sender TEXT,
            message TEXT,
            timestamp REAL
        )
    ''')
    # Вставляем сообщение в таблицу
    cursor.execute('''
        INSERT INTO messages (chat_name, sender, message, timestamp)
        VALUES (?, ?, ?, ?)
    ''', (chat_name, sender, message, time.time()))
    conn.commit()
    conn.close()

def initialize_database():
    """Создаёт файл базы данных и таблицу messages, если их нет."""
    conn = sqlite3.connect("chat_messages.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            chat_name TEXT,
            sender TEXT,
            message TEXT,
            timestamp REAL
        )
    ''')
    conn.commit()
    conn.close()

# Вызов функции при старте приложения
initialize_database()





# Функция для загрузки сообщений из базы данных
def load_messages_from_db(chat_name):
    conn = sqlite3.connect("chat_messages.db")
    cursor = conn.cursor()
    cursor.execute('''
        SELECT sender, message, timestamp FROM messages
        WHERE chat_name = ?
        ORDER BY timestamp ASC
    ''', (chat_name,))
    messages = cursor.fetchall()
    conn.close()
    return messages



class ChatScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.queue_name = None
        self.channel = rabbitmq_chat.channel  # Канал RabbitMQ

    def connect_to_chat(self):
        """Подключается к чату и загружает старые сообщения."""
        chat_name = self.ids.chat_name.text.strip()
        if not chat_name:
            self.ids.status_label.text = "Ошибка: Укажите адрес чата"
            return

        try:
            rabbitmq_chat.create_queue(chat_name)
            self.queue_name = chat_name

            # Загружаем старые сообщения
            self.load_previous_messages()

            # Запускаем поток для получения новых сообщений
            threading.Thread(target=self.consume_messages, daemon=True).start()

            self.ids.status_label.text = f"Подключено к чату '{chat_name}'"
        except Exception as e:
            self.ids.status_label.text = f"Ошибка подключения: {str(e)}"

    def send_message(self):
        """Отправляет сообщение в очередь."""
        if not self.queue_name:
            self.ids.status_label.text = "Ошибка: Подключитесь к чату"
            return

        message = self.ids.message_input.text.strip()
        if not message:
            self.ids.status_label.text = "Ошибка: Сообщение не может быть пустым"
            return

        sender = MDApp.get_running_app().current_user.get("nickname", "Anonymous")
        try:
            rabbitmq_chat.send_message(self.queue_name, sender, message)
            self.ids.message_input.text = ""  # Очищаем поле ввода
        except Exception as e:
            self.ids.status_label.text = f"Ошибка отправки сообщения: {str(e)}"

    def consume_messages(self):
        """Получает сообщения из очереди и отображает их."""

        def callback(ch, method, properties, body):
            data = json.loads(body.decode("utf-8"))
            timestamp = datetime.utcfromtimestamp(data["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
            sender = data["sender"]
            message = data["message"]

            # Сохраняем сообщение в базу данных
            save_message_to_db(self.queue_name, sender, message)

            # Обновляем интерфейс
            self.ids.chat_logs.text += f"[{timestamp}] {sender}: {message}\n"

        try:
            self.channel.basic_consume(
                queue=self.queue_name, on_message_callback=callback, auto_ack=False
            )
            self.channel.start_consuming()
        except Exception as e:
            self.ids.status_label.text = f"Ошибка получения сообщений: {str(e)}"

    def load_previous_messages(self):
        """Загружает старые сообщения из базы и очереди."""
        if not self.queue_name:
            return

        # Загружаем сообщения из базы данных
        db_messages = load_messages_from_db(self.queue_name)
        for sender, text, timestamp in db_messages:
            timestamp_str = datetime.utcfromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')
            self.ids.chat_logs.text += f"[{timestamp_str}] {sender}: {text}\n"

        # Загружаем сообщения из RabbitMQ
        queue_messages = rabbitmq_chat.get_messages(self.queue_name)
        for message in queue_messages:
            timestamp = datetime.utcfromtimestamp(message["timestamp"]).strftime('%Y-%m-%d %H:%M:%S')
            sender = message["sender"]
            text = message["message"]
            self.ids.chat_logs.text += f"[{timestamp}] {sender}: {text}\n"


class LoginScreen(Screen):
    def login(self):
        """Авторизация пользователя."""
        app = MDApp.get_running_app()
        login_screen = app.root.get_screen('login_screen')
        email = login_screen.ids.email_input.text.strip()
        password = login_screen.ids.password_input.text.strip()

        if not email or not password:
            login_screen.ids.status_label.text = "Ошибка: Заполните все поля"
            return

        try:
            # Используем словарь для передачи данных авторизации
            response = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            user_id = response.user.id

            # Получаем никнейм пользователя
            result = supabase.table("user_profiles").select("nickname").eq("id", user_id).execute()
            nickname = result.data[0]['nickname'] if result.data else None

            if not nickname:
                login_screen.ids.status_label.text = "Ошибка: Никнейм не найден"
                return

            # Сохраняем текущего пользователя
            app.current_user = {'id': user_id, 'email': email, 'nickname': nickname}
            app.change_screen("home_screen")
        except Exception as e:
            login_screen.ids.status_label.text = f"Ошибка входа: {str(e)}"


class RegisterScreen(Screen):
    def register(self):
        """Регистрация пользователя."""
        app = MDApp.get_running_app()
        register_screen = app.root.get_screen('register_screen')
        email = register_screen.ids.email_input.text.strip()
        password = register_screen.ids.password_input.text.strip()
        nickname = register_screen.ids.nickname_input.text.strip()

        if not email or not password or not nickname:
            register_screen.ids.status_label.text = "Ошибка: Заполните все поля"
            return

        try:
            # Регистрация пользователя через Supabase
            response = supabase.auth.sign_up(email=email, password=password)

            # Сохраняем nickname в таблицу user_profiles
            supabase.table("user_profiles").insert({
                "id": response.user.id,
                "nickname": nickname
            }).execute()

            app.change_screen("login_screen")
            register_screen.ids.status_label.text = "Регистрация успешна! Проверьте почту для подтверждения."
        except Exception as e:
            register_screen.ids.status_label.text = f"Ошибка регистрации: {str(e)}"


class HomeScreen(Screen):
    pass


class ProfileScreen(Screen):
    def on_pre_enter(self):
        user = MDApp.get_running_app().current_user
        self.ids.email_label.text = f"Email: {user['email']}"
        self.ids.nickname_label.text = f"Nickname: {user['nickname']}"


class RootWidget(ScreenManager):
    pass

# Настройка логирования в файл (для отладки без консоли)
logging.basicConfig(filename="app.log", level=logging.INFO, format="%(asctime)s - %(message)s")

class ChatApp(MDApp):
    current_user = None

    def build(self):
        Builder.load_file(get_resource_path("screens/login.kv"))
        Builder.load_file(get_resource_path("screens/register.kv"))
        Builder.load_file(get_resource_path("screens/home.kv"))
        Builder.load_file(get_resource_path("screens/profile.kv"))
        Builder.load_file(get_resource_path("screens/chats.kv"))

        sm = RootWidget()
        sm.add_widget(LoginScreen(name="login_screen"))
        sm.add_widget(RegisterScreen(name="register_screen"))
        sm.add_widget(HomeScreen(name="home_screen"))
        sm.add_widget(ProfileScreen(name="profile_screen"))
        sm.add_widget(ChatScreen(name="chat_screen"))

        return sm

    def change_screen(self, screen_name):
        """Смена экрана."""
        self.root.current = screen_name

    def logout(self):
        """Выход из аккаунта и переход на экран авторизации."""
        self.root.current = "login_screen"
        self.current_user = None

    def on_stop(self):
        """Вызывается при закрытии приложения."""
        logging.info("Закрытие приложения...")
        # Закрываем соединение с RabbitMQ
        try:
            rabbitmq_chat.channel.close()
            rabbitmq_chat.connection.close()
            logging.info("RabbitMQ соединение закрыто.")
        except Exception as e:
            logging.error(f"Ошибка при закрытии RabbitMQ: {e}")

        # Закрываем базу данных
        try:
            conn = sqlite3.connect("chat_messages.db")
            conn.close()
            logging.info("Соединение с базой данных закрыто.")
        except Exception as e:
            logging.error(f"Ошибка при закрытии базы данных: {e}")




if __name__ == "__main__":
    ChatApp().run()
