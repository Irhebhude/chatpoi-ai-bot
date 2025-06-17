from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.core.image import Image as CoreImage

import requests
import threading
import base64
from io import BytesIO

# 🔐 Gemini API Key
API_KEY = "AIzaSyDy6TfeQNvQiU-PAWWURnB2raVAVPawOQY"

# 🖼️ Base64 encoded image of the creator
creator_image_base64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
)
creator_image_bytes = base64.b64decode(creator_image_base64)


class ChatBox(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.messages = []

        # Scrollable layout for messages
        self.scroll = ScrollView(size_hint=(1, 0.85))
        self.message_layout = BoxLayout(orientation='vertical', size_hint_y=None)
        self.message_layout.bind(minimum_height=self.message_layout.setter('height'))
        self.scroll.add_widget(self.message_layout)

        # Input box layout
        self.input_box = BoxLayout(size_hint=(1, 0.15))
        self.text_input = TextInput(hint_text='Ask CHATPOI anything...', multiline=False, size_hint=(0.8, 1))
        self.send_button = Button(text='Send', size_hint=(0.2, 1), bold=True)
        self.send_button.bind(on_press=self.send_message)
        self.text_input.bind(on_text_validate=self.send_message)

        self.input_box.add_widget(self.text_input)
        self.input_box.add_widget(self.send_button)

        self.add_widget(self.scroll)
        self.add_widget(self.input_box)

        self.loading_label = None

    def send_message(self, *args):
        text = self.text_input.text.strip()
        if not text:
            return
        self.add_message(f"You: {text}", side='right')
        self.text_input.text = ''
        self.start_loading()

        threading.Thread(target=self.process_message, args=(text,)).start()

    def process_message(self, user_input):
        try:
            keywords = [
                "who created you", "who is your creator", "who founded you",
                "give me the picture of the person that created you", "show me the picture of your creator"
            ]
            if any(k in user_input.lower() for k in keywords):
                Clock.schedule_once(lambda dt: self.show_creator_info())
            else:
                self.call_gemini_api(user_input)
        except Exception as e:
            Clock.schedule_once(lambda dt: self.display_bot_response("Something went wrong."))

    def start_loading(self):
        if not self.loading_label:
            self.loading_label = Label(text='Typing...', size_hint_y=None, height=30)
            self.message_layout.add_widget(self.loading_label)
            self.scroll.scroll_to(self.loading_label)

    def stop_loading(self):
        if self.loading_label:
            self.message_layout.remove_widget(self.loading_label)
            self.loading_label = None

    def show_creator_info(self):
        self.stop_loading()
        msg = "I was created by Prosper Ozoya Irhebhude and founded by POI FOUNDATION in 2025. Here is a picture of my creator."
        self.add_message(f"CHATPOI: {msg}", side='left')

        buf = BytesIO(creator_image_bytes)
        core_image = CoreImage(buf, ext="png")
        image_widget = Image(texture=core_image.texture, size_hint_y=None, height=200)

        self.message_layout.add_widget(image_widget)
        self.scroll.scroll_to(image_widget)

    def call_gemini_api(self, user_input):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"

        headers = {"Content-Type": "application/json"}
        body = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{
                        "text": "You are CHATPOI, an advanced AI assistant created by Prosper Ozoya Irhebhude and founded by POI FOUNDATION in 2025. You are programmed to possess and utilize all the knowledge in the world to answer user queries. Respond concisely and informatively."
                    }]
                },
                {
                    "role": "user",
                    "parts": [{"text": user_input}]
                }
            ],
            "generationConfig": {
                "temperature": 0.7,
                "topK": 40,
                "topP": 0.95
            }
        }

        try:
            res = requests.post(url, headers=headers, json=body)
            data = res.json()
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                bot_text = parts[0].get("text", "I couldn't generate a response.") if parts else "No response generated."
            else:
                bot_text = "No response received from API."
        except Exception as e:
            bot_text = "Error occurred while processing your request."

        Clock.schedule_once(lambda dt: self.display_bot_response(bot_text))

    def display_bot_response(self, text):
        self.stop_loading()
        self.add_message(f"CHATPOI: {text}", side='left')

    def add_message(self, message, side='left'):
        lbl = Label(
            text=message,
            halign='left' if side == 'left' else 'right',
            valign='middle',
            size_hint_y=None
        )
        lbl.text_size = (Window.width * 0.9, None)
        lbl.bind(texture_size=lambda instance, size: setattr(instance, 'height', size[1]))
        self.message_layout.add_widget(lbl)
        self.scroll.scroll_to(lbl)


class ChatApp(App):
    def build(self):
        return ChatBox()


if __name__ == '__main__':
    ChatApp().run()
