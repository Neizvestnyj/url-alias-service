from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.db.crud.user import create_user, get_user_by_username
from app.schemas.user import UserCreate, UserResponse


async def create_new_user(session: AsyncSession, user_create: UserCreate) -> UserResponse:
    """
    Создаёт нового пользователя.

    :param session: Асинхронная сессия базы данных.
    :type session: AsyncSession
    :param user_create: Данные для создания пользователя.
    :type user_create: UserCreate
    :returns: Созданная запись пользователя.
    :rtype: UserResponse
    :raises ValueError: Если пользователь с таким именем уже существует.
    """
    try:
        existing_user = await get_user_by_username(session, user_create.username)
        if existing_user:
            raise ValueError("Username already exists")

        user = await create_user(session, user_create)
        return user
    except ValueError:
        raise
    except Exception as e:
        logger.error(f"Error creating user {user_create.username}: {e}")
        raise e from None
