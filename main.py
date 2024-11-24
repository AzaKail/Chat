from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivymd.app import MDApp
from supabase import create_client, Client
from kivymd.uix.screen import MDScreen
from kivymd.uix.button import MDFloatingActionButton
from kivymd.uix.snackbar import Snackbar




# Подключаем файлы разметки
Builder.load_file("screens/login.kv")
Builder.load_file("screens/chats.kv")
Builder.load_file("screens/profile.kv")

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
                self.manager.current = "chats_screen"  # Переход на экран чатов
            else:
                print("Ошибка входа: проверьте данные.")
        except Exception as e:
            print(f"Ошибка входа: {str(e)}")

    def register(self, email, password):
        """Регистрация нового пользователя через Supabase."""
        try:
            response = supabase.auth.sign_up({"email": email, "password": password})
            if response.user:
                print("Регистрация успешна! Теперь войдите.")
            else:
                print("Ошибка регистрации.")
        except Exception as e:
            print(f"Ошибка регистрации: {str(e)}")


class ChatsScreen(Screen):
    pass


class ProfileScreen(Screen):
    pass


class ChatApp(MDApp):
    current_user = None

    def build(self):
        self.title = "Chat App"
        self.theme_cls.primary_palette = "Blue"

        # Создаем менеджер экранов
        sm = ScreenManager()
        sm.add_widget(LoginScreen(name="login_screen"))
        sm.add_widget(ChatsScreen(name="chats_screen"))
        sm.add_widget(ProfileScreen(name="profile_screen"))
        return sm

    def switch_screen(self, screen_name):
        """Переключение экранов."""
        self.root.current = screen_name


if __name__ == "__main__":
    ChatApp().run()
