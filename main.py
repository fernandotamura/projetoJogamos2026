from ui.widgets import JogamosTextField  # garante registro no Factory
import os
import time
from typing import Dict

from kivy.utils import platform
from kivy.metrics import dp

from kivy.lang import Builder
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.screenmanager import ScreenManager, FadeTransition
from kivy.logger import Logger, LOG_LEVELS

from kivymd.app import MDApp
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDButton, MDButtonText, MDButtonIcon
from kivymd.uix.spinner import MDSpinner
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel

# Telas (importe ANTES de carregar os .kv)
from screens.auth import LoginScreen, SignupScreen, ForgotPasswordScreen, VerifyTokenScreen
from screens.home import HomeScreen
from screens.cadastro import CadastroScreen
from screens.sports import ChooseSportsScreen
from screens.dashboard import DashboardScreen                  # <-- você já importava, vamos usar
from screens.shell import AppShellScreen


from kivy.core.window import Window
Window.clearcolor = (0.97, 0.97, 0.98, 1)


class RootManager(ScreenManager):
    pass

class MyApp(MDApp):
    """
    App com Hot Reload custom (KV + .py), dialogs e helpers.
    Observa arquivos .kv e recarrega quando mudam.
    """
    API_BASE_URL = "http://127.0.0.1:8000"  # ou http://localhost:8000

    # Ordem de carregamento dos arquivos KV (tema primeiro)
    KV_FILES = [
        os.path.join("kv", "theme.kv"),
        os.path.join("kv", "auth.kv"),
        os.path.join("kv", "home.kv"),
        os.path.join("kv", "cadastro.kv"),
        #os.path.join("kv", "esportes.kv"),
        os.path.join("kv", "sports.kv"),
        os.path.join("kv", "dashboard.kv"),
        os.path.join("kv", "shell.kv"),
        os.path.join("kv", "viewport.kv"),   # <-- se não existir, apenas logaremos aviso
    ]

    # Pastas a observar para .py (screens)
    WATCH_PY_DIRS = [
        os.path.join(os.getcwd(), "screens"),
    ]

    _error_dialog = None
    _loader_dialog = None

    # -----------------------
    # Ciclo de vida do App
    # -----------------------
    def build(self):
        Logger.setLevel(LOG_LEVELS["debug"])
        Logger.info("App: montando UI")

        # Tema base
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.primary_hue = "600"
        self.theme_cls.theme_style = "Light"  # ou "Dark"

        # Carrega todos os KV na ordem
        for kv in self.KV_FILES:
            if os.path.exists(kv):
                try:
                    Logger.debug(f"KV: carregando {kv}")
                    Builder.load_file(kv)
                except Exception as e:
                    Logger.exception(f"KV: erro ao carregar {kv}: {e}")
            else:
                Logger.warning(f"KV: arquivo não encontrado (ok se opcional) -> {kv}")

        # Monta o ScreenManager inicial
        root = self._build_root()

        # Inicia o observador de arquivos (hot-reload)
        self._start_hot_reload()

        # Dump de telas ao iniciar (ajuda a diagnosticar navegação)
        Clock.schedule_once(lambda *_: self._debug_screens(root), 0)

        return root

    def _build_root(self) -> ScreenManager:
        """(Re)monta o ScreenManager e registra as telas."""
        sm = RootManager(transition=FadeTransition())

        # Telas públicas / auth
        sm.add_widget(LoginScreen(name="login"))
        sm.add_widget(SignupScreen(name="signup"))
        sm.add_widget(ForgotPasswordScreen(name="forgot"))
        sm.add_widget(VerifyTokenScreen(name="verify"))

        # Telas internas
        sm.add_widget(CadastroScreen(name="cadastro"))
        #sm.add_widget(EsportesScreen(name="esportes"))
        sm.add_widget(HomeScreen(name="home"))
        sm.add_widget(DashboardScreen(name="dashboard"))       # <-- ADICIONADA
        sm.add_widget(ChooseSportsScreen(name="choose_sports"))# <-- se não usar, pode remover
        sm.add_widget(AppShellScreen(name="shell"))

        # ... depois de sm.add_widget(LoginScreen(name="login")) e as demais:
        print("[Debug] telas no ScreenManager =", [s.name for s in sm.screens])
        sm.current = "login"  # GARANTE que abrimos na tela de login
        print("[Debug] tela atual =", sm.current)
        return sm

        # Primeira tela (por segurança; a 1ª adicionada já seria a atual)
        if sm.current not in sm.screen_names:
            sm.current = "login"

        return sm

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
                Logger.info(f"[HOT-RELOAD] Recarregando KV: {kv}")
                try:
                    Builder.unload_file(kv)
                except Exception as e:
                    Logger.warning(f"[HOT-RELOAD] Aviso ao descarregar {kv}: {e}")
                try:
                    Builder.load_file(kv)
                    self._kv_mtimes[kv] = current
                    kv_changed = True
                except Exception as e:
                    Logger.exception(f"[HOT-RELOAD] ERRO ao recarregar {kv}: {e}")

        # Se algum KV mudou, reconstruímos o root para aplicar novas regras
        if kv_changed:
            current_name = self.root.current if self.root else "login"
            new_root = self._build_root()
            self._swap_root(new_root, current_name)

        # 2) (Opcional) Detecta mudanças em .py e reconstrói root
        new_py_mtime = self._scan_py_mtime()
        if new_py_mtime > self._py_mtime:
            Logger.info("[HOT-RELOAD] Alteração em .py detectada. Reconstruindo telas…")
            self._py_mtime = new_py_mtime
            current_name = self.root.current if self.root else "login"
            new_root = self._build_root()
            self._swap_root(new_root, current_name)

    def _swap_root(self, new_root: ScreenManager, current_name: str):
        """Troca o root preservando a tela (se existir)."""
        try:
            self.root_window.remove_widget(self.root)
        except Exception:
            pass

        self.root = new_root
        self.root_window.add_widget(self.root)

        # Restaura a tela atual se existir; senão volta pro login
        self.root.current = current_name if current_name in self.root.screen_names else "login"
        self._debug_screens(self.root)

    # ==============
    # Helpers de UI
    # ==============
    
    def toast(self, msg: str):
        """
        Cross-platform 'toast':
        - Android: usa kivymd.toast (Toast nativo do Android).
        - Desktop (Win/Linux/macOS): usa MDSnackbar (KivyMD 2.x).
        """
        try:
            if platform == "android":
                # Android Toast
                from kivymd.toast import toast as android_toast
                android_toast(msg)
            else:
                # Snackbar no desktop
                from kivymd.uix.snackbar import (
                    MDSnackbar,
                    MDSnackbarText,
                )
                MDSnackbar(
                    MDSnackbarText(text=str(msg)),
                    y=dp(24),
                    pos_hint={"center_x": 0.5},
                    size_hint_x=0.6,
                ).open()
        except Exception as e:
            # Fallback: loga se algo der errado
            from kivy.logger import Logger
            Logger.exception(f"Toast/Snackbar fallback: {e}")

    
    def notify_error(self, msg: str, title: str = "Erro"):
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
                MDButton(
                    style="text",
                    on_release=lambda x: self._dismiss_error_dialog()
                ,
                children=[
                    MDButtonText(text="OK")
                ])
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

    # --------------------------
    # Navegação segura + debug
    # --------------------------
    def goto(self, screen_name: str):
        """Troca de tela com validação e logs amigáveis."""
        if not self.root or screen_name not in self.root.screen_names:
            msg = f"Tela '{screen_name}' não encontrada. Telas disponíveis: {self.root.screen_names if self.root else 'sem root'}"
            Logger.error(f"Navegação: {msg}")
            try:
                self.notify_error(msg, title="Navegação")
            except Exception:
                pass
            return
        Logger.info(f"Navegação: indo para '{screen_name}'")
        self.root.current = screen_name

    def _debug_screens(self, sm: ScreenManager):
        try:
            Logger.debug(f"Debug: telas no ScreenManager = {sm.screen_names}")
            Logger.debug(f"Debug: tela atual = {sm.current}")
        except Exception:
            pass


if __name__ == "__main__":
    MyApp().run()