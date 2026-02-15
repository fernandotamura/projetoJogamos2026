# screens/dashboard.py
from datetime import datetime
from kivymd.uix.screen import MDScreen
from kivy.properties import StringProperty


class DashboardScreen(MDScreen):
    greeting = StringProperty("Olá")
    user_name = StringProperty("Carol")  # depois ligamos ao backend

    def on_pre_enter(self, *args):
        # Saudação dinâmica pelo horário local (com tz do SO)
        hour = datetime.now().astimezone().hour
        if 5 <= hour < 12:
            self.greeting = "Bom dia"
        elif 12 <= hour < 18:
            self.greeting = "Boa tarde"
        else:
            self.greeting = "Boa noite"

        # Se o App expuser o nome real do usuário
        app = self._app()
        if hasattr(app, "current_user_name") and app.current_user_name:
            self.user_name = app.current_user_name

    def _app(self):
        from kivy.app import App
        return App.get_running_app()

    # ---------- Busca (modal) ----------
    _search_dialog = None

    def open_search(self):
        from kivymd.uix.dialog import MDDialog
        from kivymd.uix.boxlayout import MDBoxLayout
        from kivymd.uix.button import MDFlatButton
        from kivymd.uix.textfield import MDTextField
        from kivy.metrics import dp

        if self._search_dialog:
            try:
                self._search_dialog.open()
                return
            except Exception:
                self._search_dialog = None

        content = MDBoxLayout(orientation="vertical", spacing=dp(12), padding=(dp(8), dp(8)), adaptive_height=True)
        self._search_field = MDTextField(
            hint_text="Pesquisar...",
            helper_text="Digite sua pesquisa e pressione Enter",
            helper_text_mode="on_focus",
        )
        content.add_widget(self._search_field)

        self._search_dialog = MDDialog(
            title="Buscar",
            type="custom",
            content_cls=content,
            buttons=[
                MDFlatButton(text="Cancelar", on_release=lambda *_: self._search_dialog.dismiss()),
                MDFlatButton(text="Buscar", on_release=self._confirm_search),
            ],
        )
        self._search_dialog.open()

    def _confirm_search(self, *_):
        query = getattr(self, "_search_field", None)
        text = (query.text or "").strip() if query else ""
        if hasattr(self._app(), "toast"):
            self._app().toast(f"Buscando por: {text or 'vazio'}")
        if self._search_dialog:
            self._search_dialog.dismiss()