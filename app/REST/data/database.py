import os
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "appdb")
DB_USER = os.getenv("DB_USER", "appuser")
DB_PASSWORD = os.getenv("DB_PASSWORD", "apppassword")

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    DATABASE_URL = (
        f"postgresql+psycopg://{DB_USER}:{DB_PASSWORD}"
        f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )

engine_kwargs = {"echo": True}
if DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(
    DATABASE_URL,
    **engine_kwargs
)


# ORM BASE
class Base(DeclarativeBase):
    pass


# SESSION FACTORY
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)

# FASTAPI DEPENDENCY
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def ensure_notifications_schema_compatibility() -> None:
    """
    Keeps existing Postgres databases compatible with current notifications ORM.
    This is a lightweight migration for class project purposes.
    """
    if not DATABASE_URL.startswith("postgresql"):
        return

    with engine.begin() as connection:
        connection.exec_driver_sql(
            """
            ALTER TABLE IF EXISTS notifications
            ADD COLUMN IF NOT EXISTS idempotency_key VARCHAR
            """
        )
        connection.exec_driver_sql(
            """
            UPDATE notifications
            SET idempotency_key = 'notif_legacy_' || id::text
            WHERE idempotency_key IS NULL
            """
        )
        connection.exec_driver_sql(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS uq_notifications_idempotency_key
            ON notifications (idempotency_key)
            """
        )
