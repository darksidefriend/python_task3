from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "terms.db"

SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

# URL базы данных SQLite (файл terms.db будет создан в папке backend)
# SQLALCHEMY_DATABASE_URL = "sqlite:///./data/terms.db"

# Движок SQLAlchemy. Для SQLite нужно передать connect_args, чтобы разрешить использование в нескольких потоках
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Сессия для работы с БД
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Базовый класс для моделей
Base = declarative_base()