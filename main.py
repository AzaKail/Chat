from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivymd.app import MDApp
from supabase import create_client, Client
from kivymd.uix.screen import MDScreen
from kivymd.uix.button import MDFloatingActionButton
from kivymd.uix.snackbar import Snackbar
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton
from kivymd.uix.textfield import MDTextField




# Подключаем файлы разметки
Builder.load_file("screens/login.kv")
Builder.load_file("screens/chats.kv")
Builder.load_file("screens/profile.kv")
Builder.load_file("screens/messages.kv")


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

        def sync_user_to_userschat(user):
            supabase.table("UsersChat").insert({
                "id": user.id,
                "email": user.email,
                "created_at": user.created_at
            }).execute()


class ChatsScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.menu = None
        self.dialog = None

    def open_menu(self, button):
        if not self.menu:
            menu_items = [
                {
                    "text": "Профиль",
                    "viewclass": "OneLineListItem",
                    "on_release": lambda: self.menu_callback("profile_screen"),
                },
                {
                    "text": "Настройки",
                    "viewclass": "OneLineListItem",
                    "on_release": lambda: self.menu_callback("settings_screen"),
                },
            ]
            self.menu = MDDropdownMenu(
                caller=button,
                items=menu_items,
                width_mult=4,
            )
        self.menu.open()

    def menu_callback(self, screen_name):
        """Переключение экрана через меню."""
        self.menu.dismiss()
        self.manager.current = screen_name

    def on_pre_enter(self, *args):
        """Загружаем список чатов перед входом на экран."""
        self.load_chats()

    def load_chats(self):
        """Загрузка чатов текущего пользователя из базы данных."""
        try:
            current_user_id = MDApp.get_running_app().current_user.id
            response = supabase.table("chats").select("*").or_(
                f"user_1.eq.{current_user_id},user_2.eq.{current_user_id}"
            ).execute()

            self.ids.chats_list.clear_widgets()
            for chat in response.data:
                other_user_id = chat["user_2"] if chat["user_1"] == current_user_id else chat["user_1"]
                user_response = supabase.table("UsersChat").select("email").eq("id", other_user_id).single().execute()

                if user_response.data:
                    email = user_response.data["email"]
                    self.ids.chats_list.add_widget(
                        OneLineListItem(
                            text=email,
                            on_release=lambda x, chat_id=chat["id"]: self.open_chat(chat_id)
                        )
                    )
        except Exception as e:
            print(f"Ошибка загрузки чатов: {e}")

    def open_chat(self, chat_id):
        """Открытие чата."""
        self.manager.get_screen("messages_screen").chat_id = chat_id
        self.manager.current = "messages_screen"

    def create_new_chat(self):
        """Открытие диалога для создания нового чата."""
        if not self.dialog:
            # Создаем MDTextField и сохраняем ссылку на него
            self.email_input = MDTextField(
                hint_text="Введите email пользователя",
            )
            self.dialog = MDDialog(
                title="Создать новый чат",
                type="custom",
                content_cls=self.email_input,
                buttons=[
                    MDFlatButton(
                        text="Отмена",
                        on_release=lambda x: self.dialog.dismiss()
                    ),
                    MDFlatButton(
                        text="Создать",
                        on_release=self.start_new_chat
                    ),
                ],
            )
        self.dialog.open()

    def start_new_chat(self, *args):
        """Создание нового чата."""
        email = self.email_input.text.strip()  # Получаем email из поля ввода
        if not email:
            print("Введите email.")
            return

        try:
            # Ищем пользователя в UsersChat
            user_response = supabase.table("UsersChat").select("id").eq("email", email).single().execute()
            if not user_response.data:
                print("Пользователь с таким email не найден.")
                return

            other_user_id = user_response.data["id"]
            current_user_id = MDApp.get_running_app().current_user.id

            # Проверяем, не создаём ли чат с самим собой
            if other_user_id == current_user_id:
                print("Нельзя начать чат с самим собой.")
                return

            # Проверяем, существует ли чат
            response = supabase.table("chats").select("*").or_(
                f"user_1.eq.{current_user_id},user_2.eq.{current_user_id}"
            ).execute()

            chat = next(
                (c for c in response.data if
                 (c["user_1"] == current_user_id and c["user_2"] == other_user_id) or
                 (c["user_1"] == other_user_id and c["user_2"] == current_user_id)), None
            )

            if not chat:
                # Если чата нет, создаем новый
                chat = supabase.table("chats").insert({
                    "user_1": current_user_id,
                    "user_2": other_user_id
                }).execute().data[0]

            self.load_chats()  # Обновляем список чатов
            self.dialog.dismiss()
        except Exception as e:
            print(f"Ошибка создания чата: {e}")


class MessagesScreen(MDScreen):
    chat_id = None

    def on_pre_enter(self, *args):
        """Загружаем сообщения перед входом на экран."""
        self.load_messages()

    def load_messages(self):
        """Загрузка сообщений из базы данных."""
        try:
            messages = supabase.table("messages").select("*").eq(
                "chat_id", self.chat_id
            ).order("created_at").execute().data

            self.ids.messages_list.clear_widgets()
            for message in messages:
                alignment = "right" if message["sender_id"] == MDApp.get_running_app().current_user.id else "left"
                self.ids.messages_list.add_widget(
                    MDLabel(text=message["content"], halign=alignment)
                )
        except Exception as e:
            print(f"Ошибка загрузки сообщений: {e}")

    def send_message(self, text):
        """Отправка сообщения."""
        try:
            supabase.table("messages").insert({
                "chat_id": self.chat_id,
                "sender_id": MDApp.get_running_app().current_user.id,
                "content": text,
            }).execute()
            self.ids.message_input.text = ""
            self.load_messages()
        except Exception as e:
            print(f"Ошибка отправки сообщения: {e}")


class ProfileScreen(MDScreen):
    def on_pre_enter(self, *args):
        """Загружаем данные пользователя перед входом на экран."""
        user = MDApp.get_running_app().current_user
        if user:
            self.ids.email_label.text = f"Email: {user.email}"
            self.ids.created_at_label.text = f"Дата создания: {user.created_at}"


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
        sm.add_widget(MessagesScreen(name="messages_screen"))

        return sm

    def switch_screen(self, screen_name):
        """Переключение экранов."""
        self.root.current = screen_name


if __name__ == "__main__":
    ChatApp().run()
