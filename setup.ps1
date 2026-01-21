param(
  [switch]$Run = $false,
  [switch]$Force = $false,
  [switch]$BackendOnly = $false,
  [switch]$FrontendOnly = $false,
  [int]$Port = 8000
)

$ErrorActionPreference = "Stop"

function Write-Section($msg) {
  Write-Host ""
  Write-Host "=== $msg ===" -ForegroundColor Cyan
}

function Ensure-Dir($Path) {
  if (-not (Test-Path $Path)) {
    New-Item -ItemType Directory -Path $Path | Out-Null
    Write-Host "Criado diretório: $Path"
  } else {
    Write-Host "Diretório já existe: $Path"
  }
}

function Write-File($Path, $Content, [bool]$ForceWrite) {
  $dir = Split-Path -Parent $Path
  if ($dir -and -not (Test-Path $dir)) { Ensure-Dir $dir }
  if ((-not (Test-Path $Path)) -or $ForceWrite) {
    $Content | Out-File -FilePath $Path -Encoding utf8
    if (Test-Path $Path) { Write-Host "Gravado: $Path" -ForegroundColor Green }
  } else {
    Write-Host "Já existe (use -Force para sobrescrever): $Path" -ForegroundColor Yellow
  }
}

# Caminho raiz do projeto
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root
Write-Section "Raiz do projeto: $Root"

# 1) Estrutura de pastas
Write-Section "Criando estrutura de pastas"
Ensure-Dir "$Root\services"
Ensure-Dir "$Root\screens"
Ensure-Dir "$Root\kv"

# 2) Arquivos: requirements (backend e frontend)
Write-Section "Escrevendo requirements"
$BackendReq = @'
fastapi==0.115.5
uvicorn[standard]==0.30.6
pydantic[email]==2.8.2
pyjwt[crypto]==2.9.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.12
'@
Write-File "$Root\requirements.txt" $BackendReq $Force

$FrontendReq = @'
kivy[base]
kivymd==1.2.0
httpx==0.27.2
keyring
watchdog
'@
Write-File "$Root\requirements-frontend.txt" $FrontendReq $Force

# 3) server.py (backend FastAPI)
Write-Section "Escrevendo backend: server.py"
$ServerPy = @'
import time
from typing import Optional, Dict
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
import jwt
from passlib.hash import bcrypt

SECRET = "dev-secret"  # troque em produção
REFRESH_SECRET = "refresh-secret"
ACCESS_TTL = 900       # 15 min
REFRESH_TTL = 60 * 60 * 24 * 7  # 7 dias

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

# Mock banco
USERS: Dict[str, Dict] = {}  # email -> {password_hash, name}

class SignupIn(BaseModel):
    email: EmailStr
    password: str
    name: str

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class TokenOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

def make_token(email: str, ttl: int, secret: str):
    now = int(time.time())
    return jwt.encode({"sub": email, "iat": now, "exp": now + ttl}, secret, algorithm="HS256")

def verify_token(token: str, secret: str):
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        return payload["sub"]
    except jwt.ExpiredSignatureError:
        raise HTTPException(401, "Token expirado")
    except jwt.InvalidTokenError:
        raise HTTPException(401, "Token inválido")

def bearer_user(authorization: Optional[str] = Header(default=None)):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(401, "Credenciais ausentes")
    token = authorization.split(" ", 1)[1]
    email = verify_token(token, SECRET)
    return email

@app.post("/auth/signup", response_model=TokenOut)
def signup(data: SignupIn):
    if data.email in USERS:
        raise HTTPException(400, "E-mail já cadastrado")
    USERS[data.email] = {
        "password_hash": bcrypt.hash(data.password),
        "name": data.name,
    }
    return TokenOut(
        access_token=make_token(data.email, ACCESS_TTL, SECRET),
        refresh_token=make_token(data.email, REFRESH_TTL, REFRESH_SECRET),
    )

@app.post("/auth/login", response_model=TokenOut)
def login(data: LoginIn):
    user = USERS.get(data.email)
    if not user or not bcrypt.verify(data.password, user["password_hash"]):
        raise HTTPException(401, "Credenciais inválidas")
    return TokenOut(
        access_token=make_token(data.email, ACCESS_TTL, SECRET),
        refresh_token=make_token(data.email, REFRESH_TTL, REFRESH_SECRET),
    )

@app.post("/auth/refresh", response_model=TokenOut)
def refresh(refresh_token: str):
    email = verify_token(refresh_token, REFRESH_SECRET)
    return TokenOut(
        access_token=make_token(email, ACCESS_TTL, SECRET),
        refresh_token=make_token(email, REFRESH_TTL, REFRESH_SECRET),
    )

@app.post("/auth/forgot")
def forgot(email: EmailStr):
    # Stub: aqui você dispararia e-mail
    if email not in USERS:
        # Não vaza existência. Retorna OK mesmo assim.
        return {"status": "ok"}
    return {"status": "ok"}

@app.get("/me")
def me(user_email: str = Depends(bearer_user)):
    u = USERS[user_email]
    return {"email": user_email, "name": u["name"]}
'@
Write-File "$Root\server.py" $ServerPy $Force

# 4) Frontend: main.py
Write-Section "Escrevendo frontend: main.py"
$MainPy = @'
import os
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.uix.screenmanager import ScreenManager, FadeTransition
from kivymd.app import MDApp
from kivymd.uix.snackbar import MDSnackbar, MDSnackbarText
from services.api import ApiClient
from screens.auth import LoginScreen, ForgotPasswordScreen, SignupScreen
from screens.home import HomeScreen

class RootManager(ScreenManager):
    pass

class AuthApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.api = ApiClient()
        self.root_manager = None

    def build(self):
        # Tema inicial
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.primary_hue = "600"
        self.theme_cls.theme_style = "Light"

        # KV
        Builder.load_file(os.path.join("kv", "theme.kv"))
        Builder.load_file(os.path.join("kv", "auth.kv"))
        Builder.load_file(os.path.join("kv", "home.kv"))

        self.root_manager = RootManager(transition=FadeTransition())
        self.root_manager.add_widget(LoginScreen(name="login", app_ref=self))
        self.root_manager.add_widget(ForgotPasswordScreen(name="forgot", app_ref=self))
        self.root_manager.add_widget(SignupScreen(name="signup", app_ref=self))
        self.root_manager.add_widget(HomeScreen(name="home", app_ref=self))

        # Guarda de sessão: decide rota inicial
        Clock.schedule_once(self._guard_session, 0.1)
        return self.root_manager

    def _guard_session(self, *_):
        # Se já tem token, valida /me e vai pra home
        st, data = self.api.me()
        if st == 200:
            self.root_manager.current = "home"
            self.toast(f"Bem-vindo, {data.get('name') or data.get('email')}!")
        else:
            self.root_manager.current = "login"

    # Tema dinâmico
    def toggle_theme(self):
        self.theme_cls.theme_style = "Dark" if self.theme_cls.theme_style == "Light" else "Light"

    # Feedback helpers
    def toast(self, msg: str, color: str = "primary"):
        bar = MDSnackbar(MDSnackbarText(text=msg))
        bar.open()

    def notify_error(self, msg: str):
        self.toast(msg)

if __name__ == "__main__":
    AuthApp().run()
'@
Write-File "$Root\main.py" $MainPy $Force

# 5) services/session.py
Write-Section "Escrevendo services/session.py"
$SessionPy = @'
import json, os
from typing import Optional
from dataclasses import dataclass

KEYRING_SERVICE = "JogamosApp"
KEYRING_USER = "auth"

@dataclass
class TokenBundle:
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None

def _keyring_available():
    try:
        import keyring  # noqa
        return True
    except Exception:
        return False

def save_tokens(tokens: TokenBundle):
    if _keyring_available():
        import keyring
        keyring.set_password(KEYRING_SERVICE, "access_token", tokens.access_token or "")
        keyring.set_password(KEYRING_SERVICE, "refresh_token", tokens.refresh_token or "")
    else:
        # Fallback: arquivo na home do usuário
        path = os.path.join(os.path.expanduser("~"), ".jogamos_tokens.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"access_token": tokens.access_token, "refresh_token": tokens.refresh_token}, f)

def load_tokens() -> TokenBundle:
    if _keyring_available():
        import keyring
        a = keyring.get_password(KEYRING_SERVICE, "access_token")
        r = keyring.get_password(KEYRING_SERVICE, "refresh_token")
        return TokenBundle(a, r)
    else:
        path = os.path.join(os.path.expanduser("~"), ".jogamos_tokens.json")
        if not os.path.exists(path):
            return TokenBundle()
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return TokenBundle(data.get("access_token"), data.get("refresh_token"))

def clear_tokens():
    if _keyring_available():
        import keyring
        for key in ("access_token", "refresh_token"):
            try:
                keyring.delete_password(KEYRING_SERVICE, key)
            except Exception:
                pass
    # também limpa fallback
    path = os.path.join(os.path.expanduser("~"), ".jogamos_tokens.json")
    if os.path.exists(path):
        try:
            os.remove(path)
        except Exception:
            pass
'@
Write-File "$Root\services\session.py" $SessionPy $Force

# 6) services/api.py
Write-Section "Escrevendo services/api.py"
$ApiPy = @'
import httpx
from typing import Optional, Dict, Any, Tuple
from services.session import load_tokens, save_tokens, clear_tokens, TokenBundle

class ApiClient:
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.base_url = base_url.rstrip("/")
        self._tokens = load_tokens()

    @property
    def authorized(self) -> bool:
        return bool(self._tokens and self._tokens.access_token)

    def _auth_headers(self) -> Dict[str, str]:
        if self._tokens and self._tokens.access_token:
            return {"Authorization": f"Bearer {self._tokens.access_token}"}
        return {}

    def _save(self, access: Optional[str], refresh: Optional[str]):
        if access or refresh:
            if access: self._tokens.access_token = access
            if refresh: self._tokens.refresh_token = refresh
            save_tokens(self._tokens)

    def _refresh_if_needed(self) -> bool:
        if not self._tokens or not self._tokens.refresh_token:
            return False
        try:
            r = httpx.post(f"{self.base_url}/auth/refresh", params={"refresh_token": self._tokens.refresh_token}, timeout=10)
            r.raise_for_status()
            data = r.json()
            self._save(data.get("access_token"), data.get("refresh_token"))
            return True
        except Exception:
            clear_tokens()
            self._tokens = TokenBundle()
            return False

    def request(self, method: str, path: str, *, json: Any = None, params: Dict[str, Any] = None, require_auth=False) -> Tuple[int, Any]:
        url = f"{self.base_url}{path}"
        headers = self._auth_headers() if require_auth else {}
        try:
            r = httpx.request(method, url, json=json, params=params, headers=headers, timeout=15)
            if r.status_code == 401 and require_auth:
                # tenta refresh
                if self._refresh_if_needed():
                    headers = self._auth_headers()
                    r = httpx.request(method, url, json=json, params=params, headers=headers, timeout=15)
            status = r.status_code
            data = r.json() if r.headers.get("content-type", "").startswith("application/json") else r.text
            return status, data
        except httpx.RequestError as e:
            return 0, {"error": f"Falha de rede: {e}"}

    # ------ Endpoints ------
    def login(self, email: str, password: str):
        st, data = self.request("POST", "/auth/login", json={"email": email, "password": password})
        if st == 200:
            self._save(data.get("access_token"), data.get("refresh_token"))
        return st, data

    def signup(self, name: str, email: str, password: str):
        st, data = self.request("POST", "/auth/signup", json={"name": name, "email": email, "password": password})
        if st == 200:
            self._save(data.get("access_token"), data.get("refresh_token"))
        return st, data

    def forgot(self, email: str):
        return self.request("POST", "/auth/forgot", params={"email": email})

    def me(self):
        return self.request("GET", "/me", require_auth=True)

    def logout(self):
        clear_tokens()
        self._tokens = TokenBundle()
'@
Write-File "$Root\services\api.py" $ApiPy $Force

# 7) screens/auth.py
Write-Section "Escrevendo screens/auth.py"
$ScreensAuthPy = @'
from threading import Thread
from kivy.properties import ObjectProperty
from kivymd.uix.screen import MDScreen
from kivymd.uix.dialog import MDDialog
from kivymd.uix.spinner import MDSpinner

def run_bg(target, on_done):
    def _wrap():
        try:
            res = target()
            on_done(res, None)
        except Exception as e:
            on_done(None, e)
    Thread(target=_wrap, daemon=True).start()

class BaseAuthScreen(MDScreen):
    app_ref = ObjectProperty(None)
    _loader_dialog: MDDialog = None

    def show_loader(self, text="Carregando..."):
        if self._loader_dialog:
            return
        self._loader_dialog = MDDialog(
            title=text,
            type="custom",
            content_cls=MDSpinner(size_hint=(None, None), size=(48, 48))
        )
        self._loader_dialog.open()

    def hide_loader(self):
        if self._loader_dialog:
            self._loader_dialog.dismiss()
            self._loader_dialog = None

class LoginScreen(BaseAuthScreen):
    def do_login(self, email, password):
        if not email or not password:
            self.app_ref.notify_error("Informe e-mail e senha.")
            return
        self.show_loader("Validando credenciais...")
        def work():
            return self.app_ref.api.login(email, password)
        def done(res, err):
            self.hide_loader()
            if err:
                self.app_ref.notify_error(str(err))
                return
            st, data = res
            if st == 200:
                self.app_ref.toast("Login realizado!")
                self.app_ref.root_manager.current = "home"
            else:
                self.app_ref.notify_error(data.get("detail") if isinstance(data, dict) else str(data))
        run_bg(work, done)

class SignupScreen(BaseAuthScreen):
    def do_signup(self, name, email, password):
        if not name or not email or not password:
            self.app_ref.notify_error("Preencha todos os campos.")
            return
        self.show_loader("Criando conta...")
        def work():
            return self.app_ref.api.signup(name, email, password)
        def done(res, err):
            self.hide_loader()
            if err:
                self.app_ref.notify_error(str(err)); return
            st, data = res
            if st == 200:
                self.app_ref.toast("Cadastro concluído!")
                self.app_ref.root_manager.current = "home"
            else:
                self.app_ref.notify_error(data.get("detail") if isinstance(data, dict) else str(data))
        run_bg(work, done)

class ForgotPasswordScreen(BaseAuthScreen):
    def do_forgot(self, email):
        if not email:
            self.app_ref.notify_error("Informe o e-mail.")
            return
        self.show_loader("Enviando instruções...")
        def work():
            return self.app_ref.api.forgot(email)
        def done(res, err):
            self.hide_loader()
            if err:
                self.app_ref.notify_error(str(err)); return
            st, _ = res
            if st in (200, 204):
                self.app_ref.toast("Se o e-mail existir, enviaremos as instruções.")
                self.app_ref.root_manager.current = "login"
            else:
                self.app_ref.notify_error("Não foi possível processar a solicitação.")
        run_bg(work, done)
'@
Write-File "$Root\screens\auth.py" $ScreensAuthPy $Force

# 8) screens/home.py
Write-Section "Escrevendo screens/home.py"
$ScreensHomePy = @'
from kivy.properties import ObjectProperty
from kivymd.uix.screen import MDScreen

class HomeScreen(MDScreen):
    app_ref = ObjectProperty(None)

    def toggle_theme(self):
        self.app_ref.toggle_theme()

    def logout(self):
        self.app_ref.api.logout()
        self.app_ref.root_manager.current = "login"
        self.app_ref.toast("Sessão encerrada.")
'@
Write-File "$Root\screens\home.py" $ScreensHomePy $Force

# 9) KV files
Write-Section "Escrevendo KV files"

$ThemeKV = @'
#:import MDIconButton kivymd.uix.button.MDIconButton
#:import MDFloatLayout kivymd.uix.floatlayout.MDFloatLayout
'@
Write-File "$Root\kv\theme.kv" $ThemeKV $Force

$AuthKV = @'
#:import MDBoxLayout kivymd.uix.boxlayout.MDBoxLayout
#:import MDTextField kivymd.uix.textfield.MDTextField
#:import MDButton kivymd.uix.button.MDButton
#:import MDTopAppBar kivymd.uix.toolbar.MDTopAppBar
#:import MDLabel kivymd.uix.label.MDLabel

<RootManager>:

<LoginScreen>:
    name: "login"
    MDBoxLayout:
        orientation: "vertical"
        MDTopAppBar:
            title: "Jogamos - Login"
            left_action_items: [["account", lambda *x: None]]
        MDBoxLayout:
            orientation: "vertical"
            padding: "24dp"
            spacing: "12dp"
            MDTextField:
                id: email
                hint_text: "E-mail"
                text: ""
                helper_text: "Digite seu e-mail"
                helper_text_mode: "on_focus"
            MDTextField:
                id: password
                hint_text: "Senha"
                password: True
                text: ""
            MDButton:
                text: "Entrar"
                on_release: root.do_login(email.text, password.text)
            MDButton:
                text: "Esqueci minha senha"
                on_release: app.root_manager.current = "forgot"
            MDButton:
                text: "Criar conta"
                on_release: app.root_manager.current = "signup"

<SignupScreen>:
    name: "signup"
    MDBoxLayout:
        orientation: "vertical"
        MDTopAppBar:
            title: "Cadastro"
            left_action_items: [["arrow-left", lambda *x: app.root_manager.current = "login"]]
        MDBoxLayout:
            orientation: "vertical"
            padding: "24dp"; spacing: "12dp"
            MDTextField:
                id: name
                hint_text: "Nome"
            MDTextField:
                id: email
                hint_text: "E-mail"
            MDTextField:
                id: password
                hint_text: "Senha"
                password: True
            MDButton:
                text: "Cadastrar"
                on_release: root.do_signup(name.text, email.text, password.text)

<ForgotPasswordScreen>:
    name: "forgot"
    MDBoxLayout:
        orientation: "vertical"
        MDTopAppBar:
            title: "Recuperar Senha"
            left_action_items: [["arrow-left", lambda *x: app.root_manager.current = "login"]]
        MDBoxLayout:
            orientation: "vertical"
            padding: "24dp"; spacing: "12dp"
            MDTextField:
                id: email
                hint_text: "E-mail"
            MDButton:
                text: "Enviar instruções"
                on_release: root.do_forgot(email.text)
'@
Write-File "$Root\kv\auth.kv" $AuthKV $Force

$HomeKV = @'
#:import MDTopAppBar kivymd.uix.toolbar.MDTopAppBar
#:import MDBoxLayout kivymd.uix.boxlayout.MDBoxLayout
#:import MDButton kivymd.uix.button.MDButton
#:import MDLabel kivymd.uix.label.MDLabel

<HomeScreen>:
    name: "home"
    MDBoxLayout:
        orientation: "vertical"
        MDTopAppBar:
            title: "Jogamos - Home"
            right_action_items:
                [["theme-light-dark", lambda *x: root.toggle_theme()],
                 ["logout", lambda *x: root.logout()]]
        MDBoxLayout:
            orientation: "vertical"
            padding: "24dp"
            MDLabel:
                text: "Você está logado. :)"
                halign: "center"
'@
Write-File "$Root\kv\home.kv" $HomeKV $Force

# 10) dev.ps1 (conveniência)
Write-Section "Escrevendo dev.ps1"
$DevPs1 = @'
param(
  [switch]$BackendOnly = $false,
  [switch]$FrontendOnly = $false,
  [int]$Port = 8000
)

$ErrorActionPreference = "Stop"

function Write-Section($msg) {
  Write-Host ""
  Write-Host "=== $msg ===" -ForegroundColor Cyan
}

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

function Ensure-File($Path, $Content) {
  if (-not (Test-Path $Path)) {
    $Content | Out-File -FilePath $Path -Encoding utf8
    Write-Host "Criado: $Path"
  } else {
    Write-Host "Já existe: $Path"
  }
}

Write-Section "Checando venv"
if (-not (Test-Path "$Root\venv")) {
  Write-Host "Criando venv..."
  try { py -3 -m venv venv } catch { python -m venv venv }
} else {
  Write-Host "venv já existe."
}

$Python = Join-Path $Root "venv\Scripts\python.exe"
$Pip    = Join-Path $Root "venv\Scripts\pip.exe"

Write-Section "Atualizando pip/setuptools/wheel"
& $Python -m pip install --upgrade pip setuptools wheel

Write-Section "Instalando dependências"
if (-not $FrontendOnly) {
  & $Pip install -r "$Root\requirements.txt"
}
if (-not $BackendOnly) {
  & $Pip install -r "$Root\requirements-frontend.txt"
}

Write-Section "Inicializando"
if (-not $FrontendOnly) {
  Write-Host "Back-end: http://127.0.0.1:$Port"
  Start-Process -FilePath $Python -ArgumentList "-m","uvicorn","server:app","--reload","--host","127.0.0.1","--port",$Port `
    -WorkingDirectory $Root -WindowStyle Normal
}
if (-not $BackendOnly) {
  if (Test-Path "$Root\main.py") {
    Start-Process -FilePath $Python -ArgumentList "main.py" -WorkingDirectory $Root -WindowStyle Normal
  } else {
    Write-Host "Aviso: main.py não encontrado; pulei o frontend."
  }
}
Write-Host "Pronto. Para encerrar, feche as janelas ou use CTRL+C nelas." -ForegroundColor Green
'@
Write-File "$Root\dev.ps1" $DevPs1 $Force

# 11) venv + instalação
Write-Section "Criando/Avaliando venv"
if (-not (Test-Path "$Root\venv")) {
  try { py -3 -m venv venv } catch { python -m venv venv }
} else {
  Write-Host "venv já existe."
}

$Python = Join-Path $Root "venv\Scripts\python.exe"
$Pip    = Join-Path $Root "venv\Scripts\pip.exe"

Write-Section "Atualizando pip/setuptools/wheel"
& $Python -m pip install --upgrade pip setuptools wheel

if (-not $FrontendOnly) {
  Write-Section "Instalando dependências do backend"
  & $Pip install -r "$Root\requirements.txt"
}
if (-not $BackendOnly) {
  Write-Section "Instalando dependências do frontend"
  & $Pip install -r "$Root\requirements-frontend.txt"
}

# 12) Rodar (opcional)
if ($Run) {
  Write-Section "Subindo serviços (backend + frontend)"
  Start-Process -FilePath $Python -ArgumentList "-m","uvicorn","serer:app","--reload","--host","127.0.0.1","--port",$Port `
    -WorkingDirectory $Root -WindowStyle Normal
  if (Test-Path "$Root\main.py") {
    Start-Process -FilePath $Python -ArgumentList "main.py" -WorkingDirectory $Root -WindowStyle Normal
  }
  Write-Host "Serviços iniciados. Backend em http://127.0.0.1:$Port" -ForegroundColor Green
} else {
  Write-Host ""
  Write-Host "Setup concluído! Para rodar depois:" -ForegroundColor Green
  Write-Host "  .\dev.ps1                 # backend + frontend"
  Write-Host "  .\dev.ps1 -BackendOnly    # só backend"
  Write-Host "  .\dev.ps1 -FrontendOnly   # só frontend"
}