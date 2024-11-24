from kivymd.uix.button import MDRaisedButton
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.uix.screenmanager import Screen, ScreenManager
from kivymd.app import MDApp
from kivymd.uix.snackbar import Snackbar
from supabase import create_client, Client
from kivymd.uix.label import MDLabel
from kivy.metrics import dp
from kivy.clock import Clock

# Подключение Supabase
SUPABASE_URL = "https://olzyhnpnhadusvrryawv.supabase.co"  # Замените на ваш
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9senlobnBuaGFkdXN2cnJ5YXd2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3MzA2NjAwNzAsImV4cCI6MjA0NjIzNjA3MH0.pXJHX1HXljvAV2X1Q2cHNNfC7b6M7mtu9XuH4Tga_bg"  # Замените на ваш
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

Window.softinput_mode = "below_target"

# Подключение файлов разметки
Builder.load_file("login.kv")
Builder.load_file("chat.kv")
Builder.load_file("messages.kv")


class LoginScreen(Screen):
    def login(self, email, password):
        try:
            response = supabase.auth.sign_in_with_password({"email": email, "password": password})
            if response:
                MDApp.get_running_app().current_user = response.user
                MDApp.get_running_app().change_screen("chat_screen")
        except Exception as e:
            Snackbar(text=f"Ошибка входа: {e}").open()

    def register(self, email, password):
        if len(password) < 6:
            Snackbar(text="Пароль должен быть не менее 6 символов.").open()
            return
        try:
            response = supabase.auth.sign_up({"email": email, "password": password})
            Snackbar(text="Регистрация успешна! Пожалуйста, войдите.").open()
        except Exception as e:
            Snackbar(text=f"Ошибка регистрации: {e}").open()


class ChatScreen(Screen):
    def create_chat(self, participant_email):
        try:
            current_user_id = MDApp.get_running_app().current_user.get("id")
            participant = supabase.table("users").select("id").eq("email", participant_email).single().execute()
            if participant:
                supabase.table("chats").insert({
                    "creator_id": current_user_id,
                    "participant_id": participant["id"]
                }).execute()
                Snackbar(text="Чат создан!").open()
            else:
                Snackbar(text="Пользователь не найден!").open()
        except Exception as e:
            Snackbar(text=f"Ошибка создания чата: {e}").open()

    def open_chat(self, chat_id):
        MDApp.get_running_app().change_screen("messages_screen", chat_id=chat_id)

    def load_chats(self):
        try:
            current_user_id = MDApp.get_running_app().current_user.get("id")
            chats = supabase.table("chats").select("*").or_(
                f"creator_id.eq.{current_user_id},participant_id.eq.{current_user_id}"
            ).execute()
            chat_list = self.ids.chat_list
            chat_list.clear_widgets()

            for chat in chats["data"]:
                participant_id = chat["participant_id"] if chat["creator_id"] == current_user_id else chat["creator_id"]
                participant = supabase.table("users").select("email").eq("id", participant_id).single().execute()
                email = participant["data"]["email"] if participant["data"] else "Неизвестно"

                chat_item = MDRaisedButton(text=email, on_release=lambda x, id=chat["id"]: self.open_chat(id))
                chat_list.add_widget(chat_item)
        except Exception as e:
            Snackbar(text=f"Ошибка загрузки чатов: {e}").open()


class MessagesScreen(Screen):
    chat_id = None
    update_event = None

    def on_pre_enter(self, *args):
        self.load_messages()
        self.update_event = Clock.schedule_interval(self.load_messages, 5)

    def on_leave(self, *args):
        if self.update_event:
            Clock.unschedule(self.update_event)

    def load_messages(self):
        try:
            messages = supabase.table("messages").select("*").eq("chat_id", self.chat_id).order("created_at").execute()
            messages_list = self.ids.messages_list
            messages_list.clear_widgets()

            for message in messages["data"]:
                message_text = message["content"]
                sender_id = message["sender_id"]
                current_user_id = MDApp.get_running_app().current_user.get("id")

                alignment = "left" if sender_id != current_user_id else "right"
                messages_list.add_widget(
                    MDLabel(text=message_text, halign=alignment, size_hint_y=None, height=dp(40))
                )
        except Exception as e:
            Snackbar(text=f"Ошибка загрузки сообщений: {e}").open()

    def send_message(self, text):
        try:
            supabase.table("messages").insert({
                "chat_id": self.chat_id,
                "sender_id": MDApp.get_running_app().current_user.get("id"),
                "content": text
            }).execute()
            self.ids.message_input.text = ""
            self.load_messages()
        except Exception as e:
            Snackbar(text=f"Ошибка отправки сообщения: {e}").open()


class ChatApp(MDApp):
    current_user = None

    def build(self):
        self.title = "Chat App"
        self.theme_cls.primary_palette = "Blue"
        self.sm = ScreenManager()
        self.sm.add_widget(LoginScreen(name="login_screen"))
        self.sm.add_widget(ChatScreen(name="chat_screen"))
        self.sm.add_widget(MessagesScreen(name="messages_screen"))
        return self.sm

    def change_screen(self, screen_name, **kwargs):
        self.sm.current = screen_name
        if screen_name == "messages_screen":
            self.sm.get_screen("messages_screen").chat_id = kwargs.get("chat_id")

if __name__ == "__main__":
    ChatApp().run()
