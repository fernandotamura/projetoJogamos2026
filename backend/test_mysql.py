import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

DB_URL = os.getenv(
    "DB_URL",
    "mysql+pymysql://root@127.0.0.1:3306/jogamos?charset=utf8mb4"
)

print("DB_URL em uso:", DB_URL)  # 👈 confira se está como esperado

engine = create_engine(DB_URL, pool_pre_ping=True)

with engine.connect() as conn:
    print("SELECT 1 =>", conn.execute(text("SELECT 1")).scalar())

print("Conexão OK ✅")