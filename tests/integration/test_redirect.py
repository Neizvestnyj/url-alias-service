from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, patch

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.db.crud.url import get_url_by_short_key
from tests.utils.db_mocks import create_test_url, create_test_user


async def test_redirect_url(client: AsyncClient, async_session: AsyncSession) -> None:
    """
    Тестирует перенаправление по короткой ссылке.

    :param client: Асинхронный клиент FastAPI.
    :type client: AsyncClient
    :param async_session: Асинхронная сессия SQLAlchemy.
    :type async_session: AsyncSession
    :returns: None
    """
    user = await create_test_user(async_session, "testuser")
    url = await create_test_url(
        async_session, user_id=user["id"], original_url="https://example.com", short_key="testurl"
    )
    # Отладка: проверяем, что URL существует в базе
    db_url = await get_url_by_short_key(async_session, "testurl")
    assert db_url is not None, "URL with short_key 'testurl' not found in database"
    assert db_url.original_url == "https://example.com/"

    response = await client.get("/api/v1/r/testurl", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "https://example.com/"

    updated_url = await get_url_by_short_key(async_session, "testurl")
    assert updated_url.click_count == 1


async def test_redirect_url_expired(client: AsyncClient, async_session: AsyncSession) -> None:
    """
    Тестирует попытку перенаправления по истёкшему URL.

    :param client: Асинхронный клиент FastAPI.
    :type client: AsyncClient
    :param async_session: Асинхронная сессия SQLAlchemy.
    :type async_session: AsyncSession
    :returns: None
    """
    user = await create_test_user(async_session, "testuser")
    await create_test_url(
        async_session,
        user_id=user["id"],
        original_url="https://example.com",
        short_key="expired",
        expires_at=datetime.now(UTC) - timedelta(days=1),
    )
    response = await client.get("api/v1/r/expired")
    assert response.status_code == 410
    assert "URL has expired" in response.json()["detail"]


async def test_redirect_url_invalid(client: AsyncClient, async_session: AsyncSession) -> None:
    """
    Тестирует попытку перенаправления по неверному URL.

    :param client: Асинхронный клиент FastAPI.
    :type client: AsyncClient
    :param async_session: Асинхронная сессия SQLAlchemy.
    :type async_session: AsyncSession
    :returns: None
    """
    response = await client.get("api/v1/r/invalid")
    assert response.status_code == 404
    assert "URL not found" in response.json()["detail"]


async def test_redirect_url_internal_error(client: AsyncClient) -> None:
    """
    Тестирует обработку ошибки 500 при редиректе по короткой ссылке.

    :param client: Асинхронный клиент FastAPI.
    :returns: None
    """
    with patch("app.api.v1.redirect.redirect_to_url", new=AsyncMock(side_effect=Exception("DB crash"))):
        response = await client.get("/api/v1/r/test-crash")

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json()["detail"] == "Internal server error"
