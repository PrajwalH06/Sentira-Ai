"""
SQLite database configuration using SQLAlchemy async.
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
import os

# Use external DATABASE_URL from Render if available 
RENDER_DB_URL = os.getenv("DATABASE_URL")

if RENDER_DB_URL:
    # SQLAlchemy requires standard `postgresql+asyncpg://` dialect instead of just `postgres://`
    if RENDER_DB_URL.startswith("postgres://"):
        RENDER_DB_URL = RENDER_DB_URL.replace("postgres://", "postgresql+asyncpg://", 1)
    DATABASE_URL = RENDER_DB_URL
else:
    # Fallback to local SQLite for development
    DATABASE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
    os.makedirs(DATABASE_DIR, exist_ok=True)
    DATABASE_URL = f"sqlite+aiosqlite:///{os.path.join(DATABASE_DIR, 'sentira.db')}"

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with async_session() as session:
        yield session


async def init_db():
    async with engine.begin() as conn:
        from app.models import Feedback  # noqa: F401
        await conn.run_sync(Base.metadata.create_all)
