from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivymd.app import MDApp
from supabase import create_client, Client
from rabbitmq_chat import RabbitMQChat



# Supabase Configuration
SUPABASE_URL = "https://fywpfnnjxfohwewjsrbo.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImZ5d3Bmbm5qeGZvaHdld2pzcmJvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzI5NTI1OTYsImV4cCI6MjA0ODUyODU5Nn0.17WMM-gDxg1ENNNfIq-vNDHNaKBryiXOj31SPSlopCs"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)



import pika
import json
import threading
import time
from datetime import datetime
from kivy.uix.screenmanager import Screen

class ChatScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.connection = None
        self.channel = None
        self.queue_name = None
        self.nick = None  # Никнейм будет загружаться из Supabase

    def connect_to_chat(self):
        """Подключается к RabbitMQ и создает очередь."""
        chat_name = self.ids.chat_name.text.strip()  # Пользователь вводит адрес чата
        if not chat_name:
            self.ids.status_label.text = "Ошибка: Укажите адрес чата"
            return

        # Подключаемся к RabbitMQ
        try:
            self.connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
            self.channel = self.connection.channel()
            self.channel.queue_declare(queue=chat_name, arguments={
                'x-message-ttl': 86400000  # Время жизни сообщения (24 часа)
            })
            self.queue_name = chat_name
            self.ids.status_label.text = f"Подключено к чату '{chat_name}'"

            # Запускаем поток для получения сообщений
            consuming_thread = threading.Thread(target=self.consume_messages, daemon=True)
            consuming_thread.start()

        except Exception as e:
            self.ids.status_label.text = f"Ошибка подключения: {str(e)}"

    def send_message(self):
        """Отправляет сообщение в чат."""
        if not self.queue_name:
            self.ids.status_label.text = "Ошибка: Сначала подключитесь к чату"
            return

        message_text = self.ids.message_input.text.strip()
        if not message_text:
            self.ids.status_label.text = "Ошибка: Сообщение не может быть пустым"
            return

        # Формируем сообщение
        message = {
            'datetime': time.time(),
            'nick': self.nick,  # Никнейм из базы данных
            'msg': message_text
        }

        try:
            self.channel.basic_publish(
                exchange='',
                routing_key=self.queue_name,
                body=json.dumps(message),
                properties=pika.BasicProperties(delivery_mode=2)  # Устойчивое сообщение
            )
            self.ids.message_input.text = ""  # Очищаем поле ввода

        except Exception as e:
            self.ids.status_label.text = f"Ошибка отправки сообщения: {str(e)}"

    def consume_messages(self):
        """Получает сообщения из очереди."""
        def callback(ch, method, properties, body):
            data = json.loads(body.decode('utf-8'))

            # Форматируем сообщение
            timestamp = datetime.utcfromtimestamp(data['datetime']).strftime('%Y-%m-%d %H:%M:%S')
            sender = data['nick']
            message = data['msg']

            # Обновляем текст чата
            self.ids.chat_logs.text += f"[{timestamp}] {sender}: {message}\n"

        # Потребляем сообщения
        self.channel.basic_consume(queue=self.queue_name, on_message_callback=callback, auto_ack=True)
        self.channel.start_consuming()



class LoginScreen(Screen):
    def login(self):
        email = self.ids.email.text.strip()
        password = self.ids.password.text.strip()

        if not email or not password:
            self.ids.status_label.text = "Ошибка: Все поля обязательны для заполнения"
            return

        try:
            response = supabase.auth.sign_in_with_password({"email": email, "password": password})
            if response.user:
                user_id = response.user.id
                # Получаем данные пользователя из представления extended_users
                user_data = supabase.table("extended_users").select("*").eq("id", user_id).single().execute()
                MDApp.get_running_app().current_user = user_data.data
                self.ids.status_label.text = "Успешный вход"
                self.manager.current = "home_screen"
            else:
                self.ids.status_label.text = "Ошибка: Неверный логин или пароль"
        except Exception as e:
            print(f"Error during login: {e}")
            self.ids.status_label.text = f"Ошибка: {str(e)}"



class RegisterScreen(Screen):
    def register(self):
        email = self.ids.email.text.strip()
        password = self.ids.password.text.strip()
        nickname = self.ids.nickname.text.strip()

        if not email or not password or not nickname:
            self.ids.status_label.text = "Ошибка: Все поля обязательны для заполнения"
            return

        try:
            # Регистрация пользователя в Supabase
            response = supabase.auth.sign_up({"email": email, "password": password})
            if response.user:
                user_id = response.user.id
                # Добавляем nickname в таблицу user_profiles
                supabase.table("user_profiles").insert({
                    "id": user_id,
                    "nickname": nickname
                }).execute()
                self.ids.status_label.text = "Перейдите по почте для подтверждения регистрации"
                self.manager.current = "login_screen"
            else:
                self.ids.status_label.text = "Ошибка: Регистрация не удалась"
        except Exception as e:
            print(f"Error during registration: {e}")
            self.ids.status_label.text = f"Ошибка: {str(e)}"





class HomeScreen(Screen):
    pass


class ProfileScreen(Screen):
    def on_pre_enter(self):
        user = MDApp.get_running_app().current_user
        self.ids.email_label.text = f"Email: {user['email']}"
        self.ids.nickname_label.text = f"Nickname: {user['nickname']}"


class RootWidget(ScreenManager):
    pass


class ChatApp(MDApp):
    current_user = None

    def build(self):
        Builder.load_file("screens/login.kv")
        Builder.load_file("screens/register.kv")
        Builder.load_file("screens/home.kv")
        Builder.load_file("screens/profile.kv")
        Builder.load_file("screens/chats.kv")

        sm = RootWidget()
        sm.add_widget(LoginScreen(name="login_screen"))
        sm.add_widget(RegisterScreen(name="register_screen"))
        sm.add_widget(HomeScreen(name="home_screen"))
        sm.add_widget(ProfileScreen(name="profile_screen"))
        sm.add_widget(ChatScreen(name="chat_screen"))

        return sm



if __name__ == "__main__":
    ChatApp().run()
