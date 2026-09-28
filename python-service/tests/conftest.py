import pytest
from alembic import command
from alembic.config import Config
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.config import settings
from app.db.session import get_db
from app.main import app


@pytest.fixture(scope="session", autouse=True)
def apply_migrations():
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", settings.database_url)
    command.upgrade(alembic_cfg, "head")


async def _truncate_workflows() -> None:
    cleanup_engine = create_async_engine(
        settings.database_url,
        poolclass=NullPool,
    )
    async with cleanup_engine.begin() as conn:
        await conn.execute(text("TRUNCATE TABLE workflows RESTART IDENTITY CASCADE"))
    await cleanup_engine.dispose()


@pytest.fixture
async def client(monkeypatch):
    async def noop_close_db() -> None:
        pass

    monkeypatch.setattr("app.main.close_db", noop_close_db)

    test_engine = create_async_engine(
        settings.database_url,
        poolclass=NullPool,
    )
    test_session_factory = async_sessionmaker(test_engine, expire_on_commit=False)

    async def override_get_db():
        async with test_session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()
    await test_engine.dispose()


@pytest.fixture(autouse=True)
async def clean_db():
    await _truncate_workflows()
    yield
