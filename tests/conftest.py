from collections.abc import AsyncGenerator
import logging

from httpx import ASGITransport, AsyncClient
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.logging import logger
from app.db.models import Base
from app.db.session import get_session
from app.main import app

logging.basicConfig(level=logging.INFO)


@pytest.fixture
def anyio_backend() -> str:
    """
    Задаёт бэкенд для anyio.

    :returns: Название бэкенда.
    :rtype: str
    """
    return "asyncio"


@pytest.fixture
async def async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Предоставляет ас concepтную сессию базы данных для тестов с очисткой таблиц перед каждым тестом.

    :returns: Асинхронная сессия базы данных.
    :rtype: AsyncGenerator[AsyncSession, None]
    """
    logger.info(f"DB URL: {settings.SQLALCHEMY_TEST_DATABASE_URL}")
    async_engine = create_async_engine(settings.SQLALCHEMY_TEST_DATABASE_URL)

    # Создаем и очищаем тестовые таблицы
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(
        bind=async_engine,
        expire_on_commit=False,
        class_=AsyncSession,
    )

    async with async_session() as session:
        yield session

    await async_engine.dispose()


@pytest_asyncio.fixture
async def client(async_session: AsyncSession) -> AsyncGenerator:
    """
    Создаёт асинхронный тестовый клиент FastAPI с переопределённой зависимостью сессии.

    :param async_session: Асинхронная сессия SQLAlchemy.
    :type async_session: AsyncSession
    :returns: Асинхронный клиент FastAPI.
    :rtype: AsyncGenerator
    """

    async def override_get_session() -> AsyncSession:
        """
        Переопределяет зависимость сессии для тестов.

        :returns: Тестовая сессия.
        :rtype: AsyncSession
        """
        yield async_session

    app.dependency_overrides[get_session] = override_get_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test", follow_redirects=True) as client:
        yield client
    app.dependency_overrides.clear()
