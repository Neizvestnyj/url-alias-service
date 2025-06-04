from datetime import datetime, timedelta

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.url import URLResponse
from app.services.url_service import (
    create_short_url,
    delete_user_url,
    generate_short_key,
    get_user_urls,
    redirect_to_url,
)
from tests.utils.db_mocks import create_test_url, create_test_user


def test_generate_short_key() -> None:
    """
    Тестирует генерацию короткого ключа.

    :returns: None
    """
    key: str = generate_short_key(length=6)
    assert len(key) == 6
    assert all(c in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789" for c in key)


@pytest_asyncio.fixture
async def setup_user_and_url(async_session: AsyncSession) -> tuple[dict, URLResponse]:
    """
    Создаёт тестового пользователя и URL для тестов.

    :param async_session: Асинхронная сессия SQLAlchemy.
    :type async_session: AsyncSession
    :returns: Кортеж с данными пользователя и URL.
    :rtype: tuple[dict, URLResponse]
    """
    user: dict = await create_test_user(async_session)
    url: URLResponse = await create_test_url(async_session, user_id=user["id"])
    return user, url


async def test_create_short_url(async_session: AsyncSession) -> None:
    """
    Тестирует создание короткой ссылки с заданным ключом.

    :param async_session: Асинхронная сессия SQLAlchemy.
    :type async_session: AsyncSession
    :returns: None
    """
    user: dict = await create_test_user(async_session)
    url: URLResponse = await create_short_url(
        async_session, original_url="https://example.com", short_key="testkey", user_id=user["id"]
    )
    assert url.original_url == "https://example.com/"
    assert url.short_key == "testkey"
    assert url.user_id == user["id"]
    assert url.is_active is True


async def test_create_short_url_duplicate_key(async_session: AsyncSession) -> None:
    """
    Тестирует попытку создания ссылки с дублирующимся ключом.

    :param async_session: Асинхронная сессия SQLAlchemy.
    :type async_session: AsyncSession
    :returns: None
    """
    user: dict = await create_test_user(async_session)
    await create_short_url(async_session, original_url="https://example.com", short_key="testkey", user_id=user["id"])
    with pytest.raises(ValueError, match="Short key already exists"):
        await create_short_url(async_session, original_url="https://other.com", short_key="testkey", user_id=user["id"])


async def test_get_user_urls(async_session: AsyncSession, setup_user_and_url: tuple[dict, URLResponse]) -> None:
    """
    Тестирует получение списка URL пользователя.

    :param async_session: Асинхронная сессия SQLAlchemy.
    :type async_session: AsyncSession
    :param setup_user_and_url: Кортеж с данными пользователя и URL.
    :type setup_user_and_url: tuple[dict, URLResponse]
    :returns: None
    """
    user, _ = setup_user_and_url
    urls, total = await get_user_urls(async_session, user["id"], 1, 10)
    assert len(urls) == 1
    assert total == 1
    assert urls[0].short_key == "exmpl"


async def test_delete_user_url(async_session: AsyncSession, setup_user_and_url: tuple[dict, URLResponse]) -> None:
    """
    Тестирует удаление URL, принадлежащего пользователю.

    :param async_session: Асинхронная сессия SQLAlchemy.
    :type async_session: AsyncSession
    :param setup_user_and_url: Кортеж с данными пользователя и URL.
    :type setup_user_and_url: tuple[dict, URLResponse]
    :returns: None
    """
    user, url = setup_user_and_url
    await delete_user_url(async_session, url.id, user["id"])
    urls, total = await get_user_urls(async_session, user["id"], 1, 10)
    assert len(urls) == 0
    assert total == 0


async def test_delete_user_url_not_owner(async_session: AsyncSession) -> None:
    """
    Тестирует попытку удаления URL другим пользователем.

    :param async_session: Асинхронная сессия SQLAlchemy.
    :type async_session: AsyncSession
    :returns: None
    """
    user1: dict = await create_test_user(async_session, username="user1")
    user2: dict = await create_test_user(async_session, username="user2")
    url: URLResponse = await create_test_url(async_session, user_id=user1["id"])
    with pytest.raises(ValueError, match="Not authorized to delete this URL"):
        await delete_user_url(async_session, url.id, user2["id"])


async def test_redirect_to_url(async_session: AsyncSession, setup_user_and_url: tuple[dict, URLResponse]) -> None:
    """
    Тестирует перенаправление по короткому ключу.

    :param async_session: Асинхронная сессия SQLAlchemy.
    :type async_session: AsyncSession
    :param setup_user_and_url: Кортеж с данными пользователя и URL.
    :type setup_user_and_url: tuple[dict, URLResponse]
    :returns: None
    """
    _, url = setup_user_and_url
    original_url: str = await redirect_to_url(async_session, url.short_key)
    assert original_url == "https://example.com/"


async def test_redirect_to_url_expired(async_session: AsyncSession) -> None:
    """
    Тестирует попытку перенаправления по истёкшей ссылке.

    :param async_session: Асинхронная сессия SQLAlchemy.
    :type async_session: AsyncSession
    :returns: None
    """
    user: dict = await create_test_user(async_session)
    url: URLResponse = await create_test_url(
        async_session, user_id=user["id"], expires_at=datetime.utcnow() - timedelta(days=1)
    )
    with pytest.raises(ValueError, match="URL has expired"):
        await redirect_to_url(async_session, url.short_key)
