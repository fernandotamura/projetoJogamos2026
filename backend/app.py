import os
import secrets
import string
import smtplib
import ssl
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr, Field
from dotenv import load_dotenv

from sqlalchemy import create_engine, String, DateTime, Integer, ForeignKey, Boolean, select, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session, relationship

from passlib.context import CryptContext

# -----------------------
# .env helpers
# -----------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

def getenv_str(name: str, default: str = "") -> str:
    val = os.getenv(name)
    return default if val is None else val.strip()

def getenv_int(name: str, default: int) -> int:
    val = os.getenv(name)
    if val is None:
        return default
    val = val.strip()
    if not val:
        return default
    try:
        return int(val)
    except ValueError:
        return default

def getenv_bool(name: str, default: bool = False) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in ("1", "true", "yes", "y", "on")

# -----------------------
# Config
# -----------------------
DB_URL = getenv_str("DB_URL", "mysql+pymysql://root:@localhost:3306/jogamos?charset=utf8mb4")
DB_ECHO = getenv_bool("DB_ECHO", False)
DB_POOL_SIZE = getenv_int("DB_POOL_SIZE", 5)
DB_POOL_RECYCLE = getenv_int("DB_POOL_RECYCLE", 1800)

SMTP_HOST = getenv_str("SMTP_HOST", "")
SMTP_PORT = getenv_int("SMTP_PORT", 587)
SMTP_USER = getenv_str("SMTP_USER", "")
SMTP_PASSWORD = getenv_str("SMTP_PASSWORD", "")
SMTP_STARTTLS = getenv_bool("SMTP_STARTTLS", True)
FROM_EMAIL = getenv_str("FROM_EMAIL", "no-reply@example.com")

TOKEN_TTL_MINUTES = getenv_int("TOKEN_TTL_MINUTES", 10)

# Remove limite de 72 bytes do bcrypt puro
pwd_context = CryptContext(schemes=["bcrypt_sha256"], deprecated="auto")

# -----------------------
# SQLAlchemy setup
# -----------------------
class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"
    __table_args__ = {
        "mysql_engine": "InnoDB",
        "mysql_charset": "utf8mb4",
        "mysql_collate": "utf8mb4_unicode_ci",
    }

    email: Mapped[str] = mapped_column(String(191), primary_key=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    tokens: Mapped[list["EmailToken"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class EmailToken(Base):
    __tablename__ = "email_tokens"
    __table_args__ = {
        "mysql_engine": "InnoDB",
        "mysql_charset": "utf8mb4",
        "mysql_collate": "utf8mb4_unicode_ci",
    }

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # 🔴 TROQUE 255 -> 191 (deve bater com o PK de users.email)
    email: Mapped[str] = mapped_column(
        String(191),
        ForeignKey("users.email", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    token: Mapped[str] = mapped_column(String(16), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    user: Mapped[User] = relationship(back_populates="tokens")


engine = create_engine(
    DB_URL,
    echo=DB_ECHO,
    pool_pre_ping=True,
    pool_size=DB_POOL_SIZE,
    pool_recycle=DB_POOL_RECYCLE,
)
Base.metadata.create_all(engine)

def now_utc() -> datetime:
    return datetime.now(timezone.utc)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)

def generate_token(n: int = 6) -> str:
    # token numérico
    return "".join(secrets.choice(string.digits) for _ in range(n))

def send_email(to_email: str, subject: str, content: str) -> None:
    if not SMTP_HOST:
        # DEV: log no console
        print("========== EMAIL DEV ==========")
        print(f"Para: {to_email}")
        print(f"Assunto: {subject}")
        print(f"Conteúdo:\n{content}")
        print("================================")
        return

    msg = EmailMessage()
    msg["From"] = FROM_EMAIL
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(content)

    if SMTP_PORT == 465 and not SMTP_STARTTLS:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context) as server:
            if SMTP_USER and SMTP_PASSWORD:
                server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)
    else:
        context = ssl.create_default_context()
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            if SMTP_STARTTLS:
                server.starttls(context=context)
            if SMTP_USER and SMTP_PASSWORD:
                server.login(SMTP_USER, SMTP_PASSWORD)
            server.send_message(msg)

# -----------------------
# Schemas
# -----------------------
class SignupIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)

class VerifyIn(BaseModel):
    email: EmailStr
    token: str = Field(min_length=1, max_length=64)

class ResendIn(BaseModel):
    email: EmailStr

class LoginIn(BaseModel):
    email: EmailStr
    password: str

# -----------------------
# FastAPI app
# -----------------------
app = FastAPI(title="Auth API (MySQL)", version="2.0.0")

@app.on_event("startup")
def _startup_log():
    print("[STARTUP] DB_URL:", DB_URL)
    print("[STARTUP] SMTP_HOST:", SMTP_HOST or "(DEV mode)")
    print("[STARTUP] SMTP_PORT:", SMTP_PORT)
    print("[STARTUP] SMTP_STARTTLS:", SMTP_STARTTLS)
    print("[STARTUP] FROM_EMAIL:", FROM_EMAIL)
    try:
        print("[STARTUP] PASSLIB schemes:", pwd_context.schemes())
    except Exception as e:
        print("[STARTUP] PASSLIB error:", repr(e))

# -----------------------
# Endpoints
# -----------------------
@app.post("/auth/signup")
def signup(body: SignupIn):
    email = body.email.lower().strip()
    password = body.password

    with Session(engine) as sess:
        # existe?
        user = sess.get(User, email)
        if user:
            if user.is_verified:
                raise HTTPException(status_code=400, detail="E-mail já cadastrado e verificado.")
            # atualiza senha e data
            user.password_hash = hash_password(password)
            user.created_at = now_utc()
        else:
            user = User(email=email, password_hash=hash_password(password), is_verified=False)
            sess.add(user)

        # gera token e grava
        token = generate_token(6)
        exp = now_utc() + timedelta(minutes=TOKEN_TTL_MINUTES)
        sess.add(EmailToken(email=email, token=token, expires_at=exp))

        sess.commit()  # grava no banco antes de enviar e-mail

    # envia e-mail após commit
    try:
        send_email(
            to_email=email,
            subject="Seu token de verificação",
            content=f"Olá!\n\nSeu token de verificação é: {token}\nEle expira em {TOKEN_TTL_MINUTES} minutos.\n"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao enviar e-mail: {e}")

    return {"message": "Conta criada. Enviamos um token para seu e-mail."}

@app.post("/auth/verify-email")
def verify_email(body: VerifyIn):
    email = body.email.lower().strip()
    token_in = body.token.strip()

    with Session(engine) as sess:
        # pega o último token válido
        t = (
            sess.query(EmailToken)
            .filter(EmailToken.email == email)
            .order_by(EmailToken.id.desc())
            .first()
        )
        if not t or t.expires_at < now_utc():
            raise HTTPException(status_code=400, detail="Token não encontrado ou expirado.")
        if token_in != t.token:
            raise HTTPException(status_code=400, detail="Token inválido.")

        user = sess.get(User, email)
        if not user:
            raise HTTPException(status_code=404, detail="Usuário não encontrado.")
        user.is_verified = True
        sess.commit()

    return {"message": "E-mail verificado com sucesso."}

@app.post("/auth/resend-token")
def resend_token(body: ResendIn):
    email = body.email.lower().strip()

    with Session(engine) as sess:
        user = sess.get(User, email)
        if not user:
            raise HTTPException(status_code=404, detail="Usuário não encontrado.")
        if user.is_verified:
            raise HTTPException(status_code=400, detail="Usuário já verificado.")

        token = generate_token(6)
        exp = now_utc() + timedelta(minutes=TOKEN_TTL_MINUTES)
        sess.add(EmailToken(email=email, token=token, expires_at=exp))
        sess.commit()

    try:
        send_email(
            to_email=email,
            subject="Seu novo token de verificação",
            content=f"Olá!\n\nSeu novo token é: {token}\nEle expira em {TOKEN_TTL_MINUTES} minutos.\n"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao enviar e-mail: {e}")

    return {"message": "Novo token enviado."}

@app.post("/auth/login")
def login(body: LoginIn):
    email = body.email.lower().strip()
    password = body.password

    with Session(engine) as sess:
        user = sess.get(User, email)
        if not user:
            raise HTTPException(status_code=401, detail="Credenciais inválidas.")
        if not user.is_verified:
            raise HTTPException(status_code=403, detail="Conta ainda não verificada. Verifique seu e-mail.")

        if not verify_password(password, user.password_hash):
            raise HTTPException(status_code=401, detail="Credenciais inválidas.")

    # Se quiser emitir JWT, este é o ponto; por ora, retornamos 200 simples
    return {"message": "Login OK"}