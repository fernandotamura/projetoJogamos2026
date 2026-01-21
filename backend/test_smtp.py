import os, ssl, smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

SMTP_HOST = os.getenv("SMTP_HOST")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_STARTTLS = os.getenv("SMTP_STARTTLS", "true").lower() in ("1", "true", "yes")

TO = os.getenv("SMTP_TEST_TO", "seu-email@exemplo.com")  # opcional

print("TESTE SMTP =>", SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_STARTTLS)
msg = EmailMessage()
msg["From"] = os.getenv("FROM_EMAIL", "no-reply@example.com")
msg["To"] = TO
msg["Subject"] = "Teste SMTP (Mailtrap)"
msg.set_content("Funcionou! Este é um teste SMTP do backend.")

context = ssl.create_default_context()
with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
    if SMTP_STARTTLS:
        server.starttls(context=context)
    if SMTP_USER and SMTP_PASSWORD:
        server.login(SMTP_USER, SMTP_PASSWORD)
    server.send_message(msg)
print("OK, e-mail de teste enviado.")