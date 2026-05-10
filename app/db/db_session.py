import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


BASE_DIR = Path(__file__).resolve().parents[2]
ENV_PATH = BASE_DIR / ".env"

print("ENV_PATH:", ENV_PATH)
print("ENV_EXISTS:", ENV_PATH.exists())

load_dotenv(ENV_PATH)

settings = {
    "pguser": os.getenv("PGUSER"),
    "password": os.getenv("PASSWORD"),
    "host": os.getenv("HOST"),
    "port": os.getenv("PGPORT", "5432"),
    "pgdatabase": os.getenv("PGDATABASE"),
}


def get_engine(user: str, password: str, host: str, port: str, database: str):
    pg_query = f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{database}"
    return create_async_engine(pg_query, echo=False)


def get_settings_from_engine():
    missing = [key for key, value in settings.items() if not value]

    if missing:
        raise ValueError(f"Missing database settings: {missing}")

    return get_engine(
        user=settings["pguser"],
        password=settings["password"],
        host=settings["host"],
        port=settings["port"],
        database=settings["pgdatabase"],
    )


engine = get_settings_from_engine()

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

from app.db.base import Base
from app.db.exchange import ExchangeOperation, ExchangeFileRow

async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)