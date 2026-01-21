# services/session.py
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