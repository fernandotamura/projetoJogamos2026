import re
from kivy.app import App
from kivy.properties import StringProperty
from kivymd.uix.screen import MDScreen

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class BaseAuthScreen(MDScreen):
    @property
    def app_ref(self):
        return App.get_running_app()

    # Encaminham para o App (que mostra MDDialog/loader)
    def show_loader(self, text="Carregando..."):
        self.app_ref.show_loader(text)

    def hide_loader(self):
        self.app_ref.hide_loader()

    def notify_error(self, msg: str):
        self.app_ref.notify_error(msg)

    def toast(self, msg: str):
        self.app_ref.toast(msg)



class LoginScreen(BaseAuthScreen):
    def do_login(self, email: str, password: str):
        if not email or not password:
            self.notify_error("Informe e-mail e senha.")
            return

        self.show_loader("Validando credenciais...")
        try:
            import requests
            base_url = getattr(self.app_ref, "API_BASE_URL", "http://127.0.0.1:8000")
            url = f"{base_url}/auth/login"
            payload = {"email": email, "password": password}
            resp = requests.post(url, json=payload, timeout=15)
            st = resp.status_code
            data = resp.json() if "application/json" in resp.headers.get("content-type", "") else {"detail": resp.text}

            if st == 200:
                self.toast("Login realizado!")
                self.app_ref.root_manager.current = "home"
            else:
                detail = data.get("detail") or str(data)
                self.notify_error(detail)
        except Exception as e:
            self.notify_error(f"Erro ao fazer login: {e}")
        finally:
            self.hide_loader()

class SignupScreen(BaseAuthScreen):
    def create_account(self, email: str, password: str, confirm: str):
        if not EMAIL_REGEX.match(email):
            self.notify_error("E-mail inválido.")
            return
        if len(password) < 6:
            self.notify_error("A senha deve ter pelo menos 6 caracteres.")
            return
        if password != confirm:
            self.notify_error("As senhas não coincidem.")
            return

        self.show_loader("Criando conta e enviando token...")
        try:
            import requests
            base_url = getattr(self.app_ref, "API_BASE_URL", "http://127.0.0.1:8000")
            url = f"{base_url}/auth/signup"
            payload = {"email": email, "password": password}
            resp = requests.post(url, json=payload, timeout=15)
            st = resp.status_code
            data = resp.json() if "application/json" in resp.headers.get("content-type", "") else {"detail": resp.text}

            if st in (200, 201):
                self.toast("Conta criada! Enviamos um token para seu e-mail.")
                verify_screen = self.manager.get_screen("verify")
                verify_screen.email = email
                self.manager.current = "verify"
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
            base_url = getattr(self.app_ref, "API_BASE_URL", "http://127.0.0.1:8000")
            url = f"{base_url}/auth/verify-email"
            payload = {"email": self.email, "token": token}
            resp = requests.post(url, json=payload, timeout=15)
            st = resp.status_code
            data = resp.json() if "application/json" in resp.headers.get("content-type", "") else {"detail": resp.text}

            if st == 200:
                self.toast("Conta verificada! Faça login.")
                self.manager.current = "login"
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
            base_url = getattr(self.app_ref, "API_BASE_URL", "http://127.0.0.1:8000")
            url = f"{base_url}/auth/resend-token"
            payload = {"email": self.email}
            resp = requests.post(url, json=payload, timeout=15)
            st = resp.status_code
            data = resp.json() if "application/json" in resp.headers.get("content-type", "") else {"detail": resp.text}

            if st == 200:
                self.toast(f"Novo token enviado para {self.email}.")
            else:
                detail = data.get("detail") or str(data)
                self.notify_error(f"Falha ao reenviar token: {detail}")
        except Exception as e:
            self.notify_error(f"Erro ao reenviar token: {e}")
        finally:
            self.hide_loader()


class ForgotPasswordScreen(BaseAuthScreen):
    def send_reset(self, email: str):
        if not EMAIL_REGEX.match(email):
            self.notify_error("Informe um e-mail válido.")
            return

        # 🔧 Simulação de envio (troque pelo seu backend)
        self.toast("Se o e-mail existir, enviaremos instruções.")
        self.app_ref.root_manager.current = "login"