from unittest.mock import AsyncMock, patch

from httpx import AsyncClient
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.db.crud.url import get_url_by_short_key
from tests.utils.db_mocks import create_test_url, get_headers_and_user_id


@pytest_asyncio.fixture
async def auth_headers_and_id(async_session: AsyncSession) -> tuple[dict[str, str], int]:
    """
    Создаёт заголовки с Basic Auth для тестов.

    :param async_session: Асинхронная сессия SQLAlchemy.
    :type async_session: AsyncSession
    :returns: Заголовки с авторизацией.
    :rtype: dict
    """
    return await get_headers_and_user_id(async_session)


async def test_create_url(
    client: AsyncClient, async_session: AsyncSession, auth_headers_and_id: tuple[dict[str, str], int]
) -> None:
    """
    Тестирует создание короткой ссылки через API.

    :param client: Асинхронный клиент FastAPI.
    :type client: AsyncClient
    :param async_session: Асинхронная сессия SQLAlchemy.
    :type async_session: AsyncSession
    :param auth_headers_and_id: Заголовки с авторизацией и id пользователя.
    :type auth_headers_and_id: tuple[dict[str, str], int]
    :returns: None
    """
    payload = {"original_url": "https://example.com", "short_key": "exmpl"}
    response = await client.post("/api/v1/urls", json=payload, headers=auth_headers_and_id[0])
    assert response.status_code == 201
    data = response.json()
    assert data["original_url"] == "https://example.com/"
    assert data["short_key"] == "exmpl"
    assert data["user_id"] is not None

    url = await get_url_by_short_key(async_session, "exmpl")
    assert url is not None
    assert url.original_url == "https://example.com/"


async def test_get_user_urls(
    client: AsyncClient, async_session: AsyncSession, auth_headers_and_id: tuple[dict[str, str], int]
) -> None:
    """
    Тестирует получение списка URL пользователя.

    :param client: Асинхронный клиент FastAPI.
    :type client: AsyncClient
    :param async_session: Асинхронная сессия SQLAlchemy.
    :type async_session: AsyncSession
    :param auth_headers_and_id: Заголовки с авторизацией и id пользователя.
    :type auth_headers_and_id: tuple[dict[str, str], int]
    :returns: None
    """
    await create_test_url(async_session, user_id=auth_headers_and_id[1], short_key="testurl")
    response = await client.get("/api/v1/urls", headers=auth_headers_and_id[0])
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["short_key"] == "testurl"


async def test_successfully_delete_user_url(
    client: AsyncClient, async_session: AsyncSession, auth_headers_and_id: tuple[dict[str, str], int]
) -> None:
    """
    Тестирует удаление url.

    :param client: Асинхронный клиент FastAPI.
    :type client: AsyncClient
    :param async_session: Асинхронная сессия SQLAlchemy.
    :type async_session: AsyncSession
    :param auth_headers_and_id: Заголовки с авторизацией и id пользователя.
    :type auth_headers_and_id: tuple[dict[str, str], int]
    :returns: None
    """
    url = await create_test_url(async_session, user_id=auth_headers_and_id[1], short_key="testurl")
    response = await client.delete(f"/api/v1/urls/{url.id}", headers=auth_headers_and_id[0])
    assert response.status_code == 204


async def test_delete_not_exists_user_url(
    client: AsyncClient, async_session: AsyncSession, auth_headers_and_id: tuple[dict[str, str], int]
) -> None:
    """
    Тестирует удаление несуществующего url.

    :param client: Асинхронный клиент FastAPI.
    :type client: AsyncClient
    :param async_session: Асинхронная сессия SQLAlchemy.
    :type async_session: AsyncSession
    :param auth_headers_and_id: Заголовки с авторизацией и id пользователя.
    :type auth_headers_and_id: tuple[dict[str, str], int]
    :returns: None
    """
    response = await client.delete("/api/v1/urls/999", headers=auth_headers_and_id[0])
    assert response.status_code == 404


async def test_delete_foreign_user_url_returns_403(client: AsyncClient, async_session: AsyncSession) -> None:
    """
    Тестирует удаление url, принадлежащего другому пользователю.

    :param client: Асинхронный клиент FastAPI.
    :type client: AsyncClient
    :param async_session: Асинхронная сессия SQLAlchemy.
    :type async_session: AsyncSession
    :returns: None
    """
    headers1, user_id1 = await get_headers_and_user_id(async_session)
    headers2, user_id2 = await get_headers_and_user_id(async_session, username="test2")

    url = await create_test_url(async_session, user_id=user_id2, short_key="foreignurl")

    response = await client.delete(f"/api/v1/urls/{url.id}", headers=headers1)
    assert response.status_code == 403


async def test_delete_url_internal_error(client: AsyncClient, auth_headers_and_id: tuple[dict[str, str], int]) -> None:
    """
    Тестирует обработку ошибки 500 при удалении url.

    :param client: Асинхронный клиент FastAPI.
    :param auth_headers_and_id: Заголовки с авторизацией и id пользователя.
    :type auth_headers_and_id: tuple[dict[str, str], int]
    :returns: None
    """
    with patch("app.api.v1.urls.delete_user_url", new=AsyncMock(side_effect=Exception("DB crash"))):
        response = await client.delete("/api/v1/urls/1", headers=auth_headers_and_id[0])

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json()["detail"] == "Internal server error"
