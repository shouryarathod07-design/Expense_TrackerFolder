# Backend/db.py
import os
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base

# ------------------------------------
# 🔐 Database URL from environment
# ------------------------------------
# Prefer DATABASE_URL, but fall back to some common Render-style names
_raw_db_url = (
    os.getenv("DATABASE_URL")
    or os.getenv("DB_URL")
    or os.getenv("POSTGRES_URL")
    or os.getenv("RENDER_EXTERNAL_DATABASE_URL")
)

if not _raw_db_url:
    raise RuntimeError("❌ DATABASE_URL (or DB_URL / POSTGRES_URL) not set in environment")

# Render gives "postgresql://..." – async SQLAlchemy wants "postgresql+asyncpg://"
if _raw_db_url.startswith("postgres://"):
    _async_db_url = _raw_db_url.replace("postgres://", "postgresql+asyncpg://", 1)
elif _raw_db_url.startswith("postgresql://"):
    _async_db_url = _raw_db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
else:
    _async_db_url = _raw_db_url  # assume already correct

# ------------------------------------
# 🛠 Engine / Session / Base
# ------------------------------------
engine = create_async_engine(
    _async_db_url,
    echo=False,          # set True if you want SQL logs
    future=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)

Base = declarative_base()


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency to get an async DB session.
    """
    async with AsyncSessionLocal() as session:
        yield session
