# server.py
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