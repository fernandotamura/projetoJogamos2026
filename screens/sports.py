from kivy.properties import ListProperty
from kivymd.uix.screen import MDScreen

class ChooseSportsScreen(MDScreen):
    selected = ListProperty([])

    def toggle(self, key: str):
        if key in self.selected:
            self.selected.remove(key)
        else:
            if len(self.selected) >= 3:
                app = self._app()
                if hasattr(app, "toast"):
                    app.toast("Selecione no máximo 3 esportes.")
                return
            self.selected.append(key)

        self.update_ui()

    def update_ui(self):
        # Atualiza os cards (se estiverem definidos por ids)
        for k in ["badminton", "basquete", "bmx", "caminhada", "corrida"]:
            cid = f"card_{k}"
            if cid in self.ids:
                self.ids[cid].is_selected = (k in self.selected)

        # Botão só habilita com 3
        if "btn_done" in self.ids:
            self.ids.btn_done.disabled = (len(self.selected) != 3)

    def finish(self):
        if len(self.selected) != 3:
            app = self._app()
            if hasattr(app, "toast"):
                app.toast("Escolha exatamente 3 esportes.")
            return

        app = self._app()
        if hasattr(app, "toast"):
            app.toast("Tudo pronto!")
        # Aqui depois conectamos com backend (/user/favorites)
        # e depois podemos navegar para outra página, se quiser:
        # self.manager.current = "dashboard"

    def on_pre_enter(self, *args):
        self.update_ui()

    def _app(self):
        from kivy.app import App
        return App.get_running_app()
    
    def go_back(self):
        """
        Volta para a página inicial do Shell (dashboard).
        Como ChooseSportsScreen está dentro do MDScreenManager do shell.kv,
        self.manager é esse ScreenManager interno.
        """
        if self.manager:
            self.manager.current = "dashboard"

    def open_drawer(self):
        """
        Abre o menu hamburger (drawer) do Shell.
        O drawer fica no AppShellScreen (screen 'shell' do ScreenManager principal).
        """
        from kivy.app import App
        app = App.get_running_app()
        shell = app.root.get_screen("shell")  # ScreenManager principal → screen 'shell'
        shell.open_drawer()