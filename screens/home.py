from kivy.app import App
from kivymd.uix.screen import MDScreen


class HomeScreen(MDScreen):
    @property
    def app_ref(self):
        return App.get_running_app()

    def toggle_theme(self):
        # Alterna entre Light/Dark usando helper do App
        self.app_ref.toggle_theme()

    def go_logout(self):
        # Volta para a tela de login
        self.manager.current = "login"
