# services/api.py
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