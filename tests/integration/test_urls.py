from unittest.mock import AsyncMock, patch

from httpx import AsyncClient
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.db.crud.url import get_url_by_short_key
from app.schemas.url import URLListResponse
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


async def test_create_url_value_error(
    client: AsyncClient, async_session: AsyncSession, auth_headers_and_id: tuple[dict[str, str], int]
) -> None:
    """
    Тестирует обработку ошибки 400 при создании короткой ссылки (она уже создана).

    :param client: Асинхронный HTTP-клиент FastAPI.
    :type client: AsyncClient
    :param async_session: Асинхронная сессия SQLAlchemy.
    :type async_session: AsyncSession
    :param auth_headers_and_id: Заголовки авторизации и ID пользователя.
    :type auth_headers_and_id: tuple[dict[str, str], int]
    :raises AssertionError: Если статус ответа не 400 или сообщение не совпадает.
    :returns: None
    """
    payload = {"original_url": "https://example.com", "short_key": "exmpl"}
    await create_test_url(async_session, auth_headers_and_id[1], **payload)
    response = await client.post("/api/v1/urls", json=payload, headers=auth_headers_and_id[0])
    assert response.status_code == 400
    assert response.json()["detail"] == "Short key already exists"


async def test_create_url_internal_error(client: AsyncClient, auth_headers_and_id: tuple[dict[str, str], int]) -> None:
    """
    Тестирует обработку ошибки 500 при создании короткой ссылки.

    :param client: Асинхронный HTTP-клиент FastAPI.
    :type client: AsyncClient
    :param auth_headers_and_id: Заголовки авторизации и ID пользователя.
    :type auth_headers_and_id: tuple[dict[str, str], int]
    :raises AssertionError: Если статус ответа не 500 или сообщение не совпадает.
    :returns: None
    """
    with patch("app.api.v1.urls.create_short_url_service", new=AsyncMock(side_effect=Exception("DB crash"))):
        payload = {"original_url": "https://example.com", "short_key": "fail"}
        response = await client.post("/api/v1/urls", json=payload, headers=auth_headers_and_id[0])

    assert response.status_code == 500
    assert response.json()["detail"] == "Failed to create URL"


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
    assert len(data["items"]) == 1
    assert data["items"][0]["short_key"] == "testurl"


async def test_list_urls_pagination_and_filter(
    client: AsyncClient, async_session: AsyncSession, auth_headers_and_id: tuple[dict[str, str], int]
) -> None:
    """
    Тестирует постраничное отображение и фильтрацию URL.

    :param client: Асинхронный клиент FastAPI.
    :type client: AsyncClient
    :param async_session: Асинхронная сессия SQLAlchemy.
    :type async_session: AsyncSession
    :param auth_headers_and_id: Заголовки с авторизацией и id пользователя.
    :type auth_headers_and_id: Tuple[Dict[str, str], int]
    :returns: None
    """
    # Создаём пользователя и 15 URL (10 активных, 5 неактивных)
    user_id = auth_headers_and_id[1]
    for i in range(15):
        is_active = i < 10  # Первые 10 активны
        await create_test_url(
            async_session,
            user_id=user_id,
            short_key=f"test{i}",
            is_active=is_active,
            original_url=f"https://example.com/page{i}",
        )

    # Тест 1: Пагинация (страница 2, 5 записей, только активные)
    response = await client.get("/api/v1/urls?page=2&per_page=5&is_active=true", headers=auth_headers_and_id[0])
    assert response.status_code == 200
    data = URLListResponse.model_validate(response.json())
    assert len(data.items) == 5  # 5 записей на странице
    assert data.total == 10  # Всего 10 активных
    assert data.page == 2
    assert data.per_page == 5
    assert data.total_pages == 2  # 10 / 5 = 2 страницы
    assert all(item.is_active for item in data.items)  # Все ссылки активны
    assert data.items[0].short_key == "test4"  # Первая запись на второй странице (test4–test0)

    # Тест 2: Пагинация без фильтра (страница 1, 10 записей)
    response = await client.get("/api/v1/urls?page=1&per_page=10", headers=auth_headers_and_id[0])
    assert response.status_code == 200
    data = URLListResponse.model_validate(response.json())
    assert len(data.items) == 10  # 10 записей на странице
    assert data.total == 15  # Всего 15 ссылок
    assert data.page == 1
    assert data.per_page == 10
    assert data.total_pages == 2  # 15 / 10 = 2 страницы
    assert data.items[0].short_key == "test14"  # Самая новая ссылка

    # Тест 3: Только неактивные ссылки (страница 1, 5 записей)
    response = await client.get("/api/v1/urls?page=1&per_page=5&is_active=false", headers=auth_headers_and_id[0])
    assert response.status_code == 200
    data = URLListResponse.model_validate(response.json())
    assert len(data.items) == 5  # 5 неактивных ссылок
    assert data.total == 5  # Всего 5 неактивных
    assert data.page == 1
    assert data.per_page == 5
    assert data.total_pages == 1  # 5 / 5 = 1 страница
    assert all(not item.is_active for item in data.items)  # Все ссылки неактивны

    # Тест 4: Пустая страница (страница 3 для активных, где данных нет)
    response = await client.get("/api/v1/urls?page=3&per_page=5&is_active=true", headers=auth_headers_and_id[0])
    assert response.status_code == 200
    data = URLListResponse.model_validate(response.json())
    assert len(data.items) == 0  # Нет записей
    assert data.total == 10  # Всего 10 активных
    assert data.page == 3
    assert data.per_page == 5
    assert data.total_pages == 2  # 10 / 5 = 2 страницы


async def test_get_user_urls_internal_error(
    client: AsyncClient, auth_headers_and_id: tuple[dict[str, str], int]
) -> None:
    """
    Тестирует обработку ошибки 500 при получении url пользователей.

    :param client: Асинхронный HTTP-клиент FastAPI.
    :type client: AsyncClient
    :param auth_headers_and_id: Заголовки авторизации и ID пользователя.
    :type auth_headers_and_id: tuple[dict[str, str], int]
    :raises AssertionError: Если статус ответа не 500 или сообщение не совпадает.
    :returns: None
    """
    with patch("app.api.v1.urls.get_user_urls", new=AsyncMock(side_effect=Exception("DB crash"))):
        response = await client.get("/api/v1/urls?page=1&per_page=5&is_active=true", headers=auth_headers_and_id[0])

    assert response.status_code == 500
    assert response.json()["detail"] == "Failed to retrieve URLs"


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
