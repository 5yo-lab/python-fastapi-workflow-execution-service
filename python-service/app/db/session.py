from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

import app.models  # noqa: F401 — register models with Base.metadata

from app.config import settings

engine = create_async_engine(settings.database_url)

AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def close_db() -> None:
    await engine.dispose()


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session