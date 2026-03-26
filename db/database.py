from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker

from core.paths import get_user_data_dir

DATA_DIR = get_user_data_dir() / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "gym.sqlite3"

DATABASE_URL = f"sqlite:///{DB_PATH.as_posix()}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    future=True,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()


def _apply_sqlite_migrations() -> None:
    with engine.begin() as conn:
        columns = {
            row[1]
            for row in conn.execute(text("PRAGMA table_info(ejercicios)")).fetchall()
        }

        if "descanso_segundos" not in columns:
            conn.execute(
                text(
                    "ALTER TABLE ejercicios ADD COLUMN descanso_segundos INTEGER NOT NULL DEFAULT 30"
                )
            )

        if "rondas" not in columns:
            conn.execute(
                text("ALTER TABLE ejercicios ADD COLUMN rondas INTEGER NOT NULL DEFAULT 1")
            )


def init_db() -> None:
    # Import models before create_all so metadata is fully registered.
    from db import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _apply_sqlite_migrations()
