from kivy.lang import Builder
from kivy.uix.screenmanager import Screen, ScreenManager
from kivymd.app import MDApp
from kivymd.uix.snackbar import Snackbar
from supabase import create_client, Client

# Подключаем файл разметки
Builder.load_file("screens/login.kv")

# Конфигурация Supabase
SUPABASE_URL = "https://olzyhnpnhadusvrryawv.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9senlobnBuaGFkdXN2cnJ5YXd2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzA2NjAwNzAsImV4cCI6MjA0NjIzNjA3MH0.pXJHX1HXljvAV2X1Q2cHNNfC7b6M7mtu9XuH4Tga_bg"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

class LoginScreen(Screen):
    def login(self, email, password):
        """Вход пользователя через Supabase."""
        try:
            response = supabase.auth.sign_in_with_password({"email": email, "password": password})
            if response.user:
                MDApp.get_running_app().current_user = response.user
                self.show_snackbar(f"Добро пожаловать, {response.user.email}!")
            else:
                self.show_snackbar("Ошибка входа: проверьте данные.")
        except Exception as e:
            self.show_snackbar(f"Ошибка входа: {str(e)}")

    def register(self, email, password):
        """Регистрация нового пользователя через Supabase."""
        try:
            response = supabase.auth.sign_up({"email": email, "password": password})
            if response.user:
                self.show_snackbar("Регистрация успешна! Теперь войдите.")
            else:
                self.show_snackbar("Ошибка регистрации.")
        except Exception as e:
            self.show_snackbar(f"Ошибка регистрации: {str(e)}")

    def show_snackbar(self, message):
        """Показываем сообщение с помощью Snackbar."""
        Snackbar(text=message).open()


class ChatApp(MDApp):
    current_user = None

    def build(self):
        self.title = "Chat App"
        self.theme_cls.primary_palette = "Blue"

        # Создаем менеджер экранов
        sm = ScreenManager()
        sm.add_widget(LoginScreen(name="login_screen"))
        return sm


if __name__ == "__main__":
    ChatApp().run()