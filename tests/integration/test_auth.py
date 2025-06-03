from unittest.mock import AsyncMock, patch

from httpx import AsyncClient
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status

from app.db.crud.user import get_user_by_username
from tests.utils.db_mocks import create_test_user


@pytest_asyncio.fixture
async def registered_user(async_session: AsyncSession) -> dict:
    """
    Создаёт зарегистрированного пользователя для тестов.

    :param async_session: Асинхронная сессия SQLAlchemy.
    :type async_session: AsyncSession
    :returns: Данные пользователя.
    :rtype: Dict
    """
    user = await create_test_user(async_session, username="testuser", password="testpass")
    return user


async def test_register_user_success(client: AsyncClient, async_session: AsyncSession) -> None:
    """
    Тестирует регистрацию нового пользователя через API.

    :param client: Асинхронный клиент FastAPI.
    :type client: AsyncClient
    :param async_session: Асинхронная сессия SQLAlchemy.
    :type async_session: AsyncSession
    :returns: None
    """
    payload = {"username": "newuser", "password": "newpass123"}
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "newuser"
    assert "id" in data
    assert "created_at" in data

    # Проверка записи в базе
    user = await get_user_by_username(async_session, "newuser")
    assert user is not None
    assert user.username == "newuser"


async def test_register_user_duplicate(client: AsyncClient, registered_user: dict) -> None:
    """
    Тестирует попытку регистрации пользователя с существующим именем.

    :param client: Асинхронный клиент FastAPI.
    :type client: AsyncClient
    :param registered_user: Данные зарегистрированного пользователя.
    :type registered_user: Dict
    :returns: None
    """
    payload = {"username": registered_user["username"], "password": "testpass"}
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 400
    assert "Username already exists" in response.json()["detail"]


async def test_register_user_internal_error(client: AsyncClient) -> None:
    """
    Тестирует ситуацию, когда при регистрации происходит непредвиденная ошибка (500).

    :param client: Асинхронный клиент FastAPI.
    :returns: None
    """
    payload = {"username": "crashuser", "password": "somepass"}

    # Патчим функцию create_new_user, чтобы выбрасывала исключение
    with patch("app.api.v1.auth.create_new_user", new=AsyncMock(side_effect=Exception("DB crash"))):
        response = await client.post("/api/v1/auth/register", json=payload)

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json()["detail"] == "Failed to register user"
