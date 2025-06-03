import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.user import UserCreate, UserResponse
from app.services.user_service import create_new_user
from tests.utils.db_mocks import create_test_user


async def test_create_new_user(async_session: AsyncSession) -> None:
    """
    Тестирует создание нового пользователя.

    :param async_session: Асинхронная сессия SQLAlchemy.
    :type async_session: AsyncSession
    :returns: None
    """
    user_create = UserCreate(username="newuser", password="newpass123")
    user: UserResponse = await create_new_user(async_session, user_create)
    assert user.username == "newuser"
    assert user.id is not None
    assert user.created_at is not None


async def test_create_new_user_duplicate_username(async_session: AsyncSession) -> None:
    """
    Тестирует попытку создания пользователя с существующим именем.

    :param async_session: Асинхронная сессия SQLAlchemy.
    :type async_session: AsyncSession
    :returns: None
    """
    await create_test_user(async_session, username="dupuser")
    user_create = UserCreate(username="dupuser", password="pass123")
    with pytest.raises(ValueError, match="Username already exists"):
        await create_new_user(async_session, user_create)
