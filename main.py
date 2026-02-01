import os
import time
from typing import Dict
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, FadeTransition
from kivy.clock import Clock
from kivymd.app import MDApp  # usamos o MDApp "normal" aqui
from kivy.metrics import dp

# Telas (importe ANTES de carregar os .kv)
from screens.auth import LoginScreen, SignupScreen, ForgotPasswordScreen, VerifyTokenScreen
from screens.home import HomeScreen
from screens.cadastro import CadastroScreen  # ⬅️ nova tela de cadastro
from screens.esportes import EsportesScreen

# Diálogos e componentes de UI
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton
from kivymd.uix.spinner import MDSpinner
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel


class RootManager(ScreenManager):
    pass


class MyApp(MDApp):
    """
    App com Hot Reload custom (sem HotReloadViewer), dialogs e helpers.
    Observa arquivos .kv e recarrega quando mudam.
    """
    API_BASE_URL = "http://127.0.0.1:8000"  # ou http://localhost:8000
    # Liste **na ordem** em que quer carregar os KV (tema primeiro)
    KV_FILES = [
        os.path.join("kv", "theme.kv"),
        os.path.join("kv", "auth.kv"),
        os.path.join("kv", "home.kv"),
        os.path.join("kv", "cadastro.kv"),  # ⬅️ novo KV da tela de cadastro
        os.path.join("kv", "esportes.kv"),
    ]

    # Pastas a observar para .py (screens) — se quiser rebuild do root ao alterar lógica
    WATCH_PY_DIRS = [
        os.path.join(os.getcwd(), "screens"),
    ]

    _error_dialog = None
    _loader_dialog = None

    # -----------------------
    # Ciclo de vida do App
    # -----------------------
    def build(self):
        # Tema base
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.primary_hue = "600"
        self.theme_cls.theme_style = "Light"  # ou "Dark"

        # Carrega todos os KV na ordem
        for kv in self.KV_FILES:
            if os.path.exists(kv):
                Builder.load_file(kv)
            else:
                print(f"[AVISO] KV não encontrado: {kv}")

        # Monta o ScreenManager inicial
        root = self._build_root()
        # Inicia o observador de arquivos (hot-reload)
        self._start_hot_reload()
        return root

    def _build_root(self) -> ScreenManager:
        """(Re)monta o ScreenManager e registra as telas."""
        root = RootManager(transition=FadeTransition())
        root.add_widget(LoginScreen(name="login"))
        root.add_widget(SignupScreen(name="signup"))
        root.add_widget(ForgotPasswordScreen(name="forgot"))
        root.add_widget(VerifyTokenScreen(name="verify"))
        root.add_widget(CadastroScreen(name="cadastro"))  # ⬅️ nova tela adicionada
        root.add_widget(EsportesScreen(name="esportes"))
        root.add_widget(HomeScreen(name="home"))
        return root

    # -----------------------------------
    # Hot Reload (KV + opcionalmente .py)
    # -----------------------------------
    def _start_hot_reload(self):
        """Inicia um agendador que observa alterações em KV e (opcional) .py."""
        # Mapa caminho -> última modificação
        self._kv_mtimes: Dict[str, float] = {}
        for kv in self.KV_FILES:
            try:
                self._kv_mtimes[kv] = os.path.getmtime(kv)
            except FileNotFoundError:
                self._kv_mtimes[kv] = 0.0

        # (Opcional) observar .py das pastas registradas
        self._py_mtime = self._scan_py_mtime()

        # Checa a cada 0.7s
        Clock.schedule_interval(self._poll_changes, 0.7)

    def _scan_py_mtime(self) -> float:
        """Retorna o maior mtime entre os .py observados em WATCH_PY_DIRS."""
        max_mtime = 0.0
        for d in self.WATCH_PY_DIRS:
            if not os.path.isdir(d):
                continue
            for root, _, files in os.walk(d):
                for f in files:
                    if f.endswith(".py"):
                        path = os.path.join(root, f)
                        try:
                            mt = os.path.getmtime(path)
                            if mt > max_mtime:
                                max_mtime = mt
                        except FileNotFoundError:
                            pass
        return max_mtime

    def _poll_changes(self, *args):
        """Verifica alterações e aplica hot reload."""
        # 1) Recarrega KV alterados, mantendo ordem
        kv_changed = False
        for kv in self.KV_FILES:
            try:
                current = os.path.getmtime(kv)
            except FileNotFoundError:
                current = 0.0
            if current > self._kv_mtimes.get(kv, 0.0):
                print(f"[HOT-RELOAD] Recarregando KV: {kv}")
                try:
                    # Descarrrega e recarrega o KV
                    Builder.unload_file(kv)
                except Exception as e:
                    print(f"[HOT-RELOAD] Aviso ao descarregar {kv}: {e}")
                try:
                    Builder.load_file(kv)
                    self._kv_mtimes[kv] = current
                    kv_changed = True
                except Exception as e:
                    print(f"[HOT-RELOAD] ERRO ao recarregar {kv}: {e}")

        # Se algum KV mudou, reconstruímos o root para aplicar novas regras
        if kv_changed:
            # Guarda a tela atual para restaurar se possível
            current_name = self.root.current if self.root else "login"
            # Reconstrói o ScreenManager
            new_root = self._build_root()
            # Substitui o root do App
            self._swap_root(new_root, current_name)

        # 2) (Opcional) Detecta mudanças em .py e reconstrói root
        new_py_mtime = self._scan_py_mtime()
        if new_py_mtime > self._py_mtime:
            print("[HOT-RELOAD] Alteração em .py detectada. Reconstruindo telas…")
            self._py_mtime = new_py_mtime
            current_name = self.root.current if self.root else "login"
            new_root = self._build_root()
            self._swap_root(new_root, current_name)

    def _swap_root(self, new_root: ScreenManager, current_name: str):
        """Troca o root preservando a tela (se existir)."""
        try:
            # troca o root
            self.root_window.remove_widget(self.root)
        except Exception:
            pass
        self.root = new_root
        self.root_window.add_widget(self.root)
        # Restaura a tela atual se existir
        if current_name in self.root.screen_names:
            self.root.current = current_name

    # ==============
    # Helpers de UI
    # ==============
    def toast(self, msg: str):
        from kivymd.toast import toast as md_toast
        md_toast(msg)

    def notify_error(self, msg: str, title: str = "Erro"):
        """Mostra um MDDialog simples de erro."""
        if self._error_dialog:
            try:
                self._error_dialog.dismiss()
            except Exception:
                pass
            self._error_dialog = None

        self._error_dialog = MDDialog(
            title=title,
            text=str(msg),
            buttons=[
                MDFlatButton(text="OK", on_release=lambda x: self._dismiss_error_dialog())
            ],
        )
        self._error_dialog.open()

    def _dismiss_error_dialog(self, *args):
        if self._error_dialog:
            self._error_dialog.dismiss()
            self._error_dialog = None

    def show_loader(self, text: str = "Carregando..."):
        """Exibe um diálogo com spinner (loader)."""
        if self._loader_dialog:
            # Atualiza o texto se já existir
            content = self._loader_dialog.content_cls
            for child in content.children:
                if isinstance(child, MDLabel):
                    child.text = text
            return

        content = MDBoxLayout(
            orientation="horizontal",
            spacing=dp(16),
            padding=(dp(16), dp(16)),
            adaptive_height=True,
        )
        spinner = MDSpinner(size_hint=(None, None), size=(dp(32), dp(32)))
        label = MDLabel(text=text)
        content.add_widget(spinner)
        content.add_widget(label)

        self._loader_dialog = MDDialog(
            type="custom",
            content_cls=content,
            auto_dismiss=False,
        )
        self._loader_dialog.open()

    def hide_loader(self):
        if self._loader_dialog:
            self._loader_dialog.dismiss()
            self._loader_dialog = None

    def toggle_theme(self):
        """Alterna Light/Dark; usado pela Home."""
        self.theme_cls.theme_style = "Dark" if self.theme_cls.theme_style == "Light" else "Light"

    @property
    def root_manager(self):
        return self.root


if __name__ == "__main__":
    MyApp().run()