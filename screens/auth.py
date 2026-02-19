import re
from kivy.app import App
from kivy.properties import StringProperty
from kivymd.uix.screen import MDScreen
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout

# Fallbacks (KivyMD 2.x / MD3)
from kivy.metrics import dp
from kivymd.uix.snackbar import MDSnackbar, MDSnackbarText

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class BaseAuthScreen(MDScreen):
    # --- Referência segura ao App ---
    @property
    def app(self):
        """Retorna a instância atual do MDApp."""
        return App.get_running_app()

    # --- Navegação centralizada ---
    def goto(self, screen_name: str):
        """
        Tenta navegar usando:
          1) app.goto(name) se existir,
          2) app.root_manager.current = name se existir,
          3) self.manager.current = name (fallback padrão).
        """
        _app = self.app
        if hasattr(_app, "goto"):
            try:
                _app.goto(screen_name)
                return
            except Exception:
                pass

        if hasattr(_app, "root_manager") and getattr(_app, "root_manager", None):
            try:
                _app.root_manager.current = screen_name
                return
            except Exception:
                pass

        # Fallback absoluto
        if self.manager:
            self.manager.current = screen_name

    # --- Loaders / feedback visual ---
    def show_loader(self, text: str = "Carregando..."):
        _app = self.app
        if hasattr(_app, "show_loader"):
            try:
                _app.show_loader(text)
                return
            except Exception:
                pass
        # Fallback: snackbar
        MDSnackbar(
            MDSnackbarText(text=str(text)),
            y=dp(24),
            pos_hint={"center_x": 0.5},
            size_hint_x=0.6,
        ).open()

    def hide_loader(self):
        _app = self.app
        if hasattr(_app, "hide_loader"):
            try:
                _app.hide_loader()
                return
            except Exception:
                pass
        # Fallback: nada a fazer para snackbar simples

    def notify_error(self, msg: str):
        _app = self.app
        if hasattr(_app, "notify_error"):
            try:
                _app.notify_error(str(msg))
                return
            except Exception:
                pass
        # Fallback: snackbar
        MDSnackbar(
            MDSnackbarText(text=str(msg)),
            y=dp(24),
            pos_hint={"center_x": 0.5},
            size_hint_x=0.8,
        ).open()

    def toast(self, msg: str):
        _app = self.app
        if hasattr(_app, "toast"):
            try:
                _app.toast(str(msg))
                return
            except Exception:
                pass
        # Fallback: snackbar
        MDSnackbar(
            MDSnackbarText(text=str(msg)),
            y=dp(24),
            pos_hint={"center_x": 0.5},
            size_hint_x=0.6,
        ).open()


class LoginScreen(BaseAuthScreen):

    def on_kv_post(self, *args):
            # SENTINELA: cria uma faixa se nada for adicionado/visível
            if not self.children:
                box = MDBoxLayout(md_bg_color=(1, 0, 0, 0.15))  # vermelho translúcido
                box.add_widget(MDLabel(text="SENTINELA LOGIN", halign="center"))
                self.add_widget(box)

    def do_login(self, email: str, password: str):
        email = (email or "").strip()
        password = password or ""

        if not email or not password:
            self.notify_error("Informe e-mail e senha.")
            return

        self.show_loader("Validando credenciais...")
        try:
            import requests

            base_url = getattr(self.app, "API_BASE_URL", "http://127.0.0.1:8000")
            url = f"{base_url}/auth/login"
            payload = {"email": email, "password": password}

            resp = requests.post(url, json=payload, timeout=15)
            st = resp.status_code
            ctype = resp.headers.get("content-type", "")
            data = resp.json() if "application/json" in ctype else {"detail": resp.text}

            if st == 200:
                self.toast("Login realizado!")
                # Ajuste a tela alvo conforme seu fluxo:
                # "dashboard" (pelo seu log) ou "shell"/"home"
                self.goto("dashboard")
            else:
                detail = data.get("detail") or str(data)
                self.notify_error(detail)
        except Exception as e:
            self.notify_error(f"Erro ao fazer login: {e}")
        finally:
            self.hide_loader()


class SignupScreen(BaseAuthScreen):
    def create_account(self, email: str, password: str, confirm: str):
        email = (email or "").strip()
        if not EMAIL_REGEX.match(email):
            self.notify_error("E-mail inválido.")
            return
        if len(password or "") < 6:
            self.notify_error("A senha deve ter pelo menos 6 caracteres.")
            return
        if (password or "") != (confirm or ""):
            self.notify_error("As senhas não coincidem.")
            return

        self.show_loader("Criando conta e enviando token...")
        try:
            import requests

            base_url = getattr(self.app, "API_BASE_URL", "http://127.0.0.1:8000")
            url = f"{base_url}/auth/signup"
            payload = {"email": email, "password": password}

            resp = requests.post(url, json=payload, timeout=15)
            st = resp.status_code
            ctype = resp.headers.get("content-type", "")
            data = resp.json() if "application/json" in ctype else {"detail": resp.text}

            if st in (200, 201):
                self.toast("Conta criada! Enviamos um token para seu e-mail.")
                verify_screen = self.manager.get_screen("verify")
                verify_screen.email = email
                self.goto("verify")
            else:
                detail = data.get("detail") or str(data)
                self.notify_error(f"Falha ao criar conta: {detail}")
        except Exception as e:
            self.notify_error(f"Erro ao criar conta: {e}")
        finally:
            self.hide_loader()


class VerifyTokenScreen(BaseAuthScreen):
    email = StringProperty("")

    def verify_token(self, token: str):
        token = (token or "").strip()
        if not token:
            self.notify_error("Informe o token.")
            return
        if not self.email:
            self.notify_error("E-mail não definido nesta verificação.")
            return

        self.show_loader("Validando token...")
        try:
            import requests

            base_url = getattr(self.app, "API_BASE_URL", "http://127.0.0.1:8000")
            url = f"{base_url}/auth/verify-email"
            payload = {"email": self.email, "token": token}

            resp = requests.post(url, json=payload, timeout=15)
            st = resp.status_code
            ctype = resp.headers.get("content-type", "")
            data = resp.json() if "application/json" in ctype else {"detail": resp.text}

            if st == 200:
                self.toast("Conta verificada! Faça login.")
                self.goto("login")
            else:
                detail = data.get("detail") or str(data)
                self.notify_error(f"Não foi possível verificar: {detail}")
        except Exception as e:
            self.notify_error(f"Erro ao verificar: {e}")
        finally:
            self.hide_loader()

    def resend_token(self):
        if not self.email:
            self.notify_error("E-mail não definido nesta verificação.")
            return

        self.show_loader("Reenviando token...")
        try:
            import requests

            base_url = getattr(self.app, "API_BASE_URL", "http://127.0.0.1:8000")
            url = f"{base_url}/auth/resend-token"
            payload = {"email": self.email}

            resp = requests.post(url, json=payload, timeout=15)
            st = resp.status_code
            ctype = resp.headers.get("content-type", "")
            data = resp.json() if "application/json" in ctype else {"detail": resp.text}

            if st == 200:
                self.toast(f"Novo token enviado para {self.email}.")
            else:
                detail = data.get("detail") or str(data)
                self.notify_error(f"Falha ao reenviar token: {detail}")
        except Exception as e:
            self.notify_error(f"Erro ao reenviar: {e}")
        finally:
            self.hide_loader()


class ForgotPasswordScreen(BaseAuthScreen):
    def send_reset(self, email: str):
        email = (email or "").strip()
        if not EMAIL_REGEX.match(email):
            self.notify_error("Informe um e-mail válido.")
            return

        # TODO: integrar com backend real
        self.toast("Se o e-mail existir, enviaremos instruções.")
        self.goto("login")