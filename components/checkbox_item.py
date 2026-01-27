from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.selectioncontrol import MDCheckbox
from kivymd.uix.label import MDLabel
from kivy.uix.image import Image

class MDCheckboxItem(MDBoxLayout):
    def __init__(self, text="", icon_path=None, **kwargs):
        super().__init__(orientation="horizontal", spacing=10, padding=10, **kwargs)
        self.text = text
        self.active = False

        self.checkbox = MDCheckbox()
        self.checkbox.bind(active=self.on_active)

        if icon_path:
            # Usando Image do Kivy
            self.icon = Image(source=icon_path, size_hint=(None, None), size=(40, 40))
            self.add_widget(self.icon)

        self.label = MDLabel(text=text, halign="left")

        self.add_widget(self.checkbox)
        self.add_widget(self.label)

    def on_active(self, checkbox, value):
        self.active = value

