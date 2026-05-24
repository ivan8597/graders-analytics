import os
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

API_URL = os.getenv("API_URL", "https://b2b.itresume.ru/api/statistics")
API_CLIENT = os.getenv("API_CLIENT", "Skillfactory")
API_CLIENT_KEY = os.getenv("API_CLIENT_KEY", "")

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "grader_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

LOGS_DIR = os.getenv("LOGS_DIR", "logs")


def get_db_config() -> dict[str, str]:
    return {
        "host": DB_HOST,
        "port": DB_PORT,
        "database": DB_NAME,
        "user": DB_USER,
        "password": DB_PASSWORD,
    }


def get_db_engine() -> Engine:
    password = quote_plus(DB_PASSWORD)
    url = f"postgresql+psycopg2://{DB_USER}:{password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    return create_engine(url)


def validate_config() -> None:
    if not API_CLIENT_KEY:
        raise ValueError(
            "API_CLIENT_KEY не задан. Скопируйте .env.example в .env и заполните значения."
        )
