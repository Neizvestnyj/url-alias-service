from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.auth.utils import get_password_hash
from app.core.logging import logger
from app.db.models import User
from app.schemas.user import UserCreate, UserResponse


async def create_user(session: AsyncSession, user_create: UserCreate) -> UserResponse:
    """
    Создаёт нового пользователя в базе данных.

    :param session: Асинхронная сессия базы данных.
    :type session: AsyncSession
    :param user_create: Данные для создания пользователя.
    :type user_create: UserCreate
    :returns: Созданная запись пользователя.
    :rtype: UserResponse
    """
    try:
        hashed_password = get_password_hash(user_create.password)
        db_user = User(username=user_create.username, hashed_password=hashed_password)
        session.add(db_user)
        await session.commit()
        await session.refresh(db_user)
        logger.info(f"Created user: {user_create.username}")
        return UserResponse.model_validate(db_user)
    except Exception as e:
        logger.error(f"Error creating user {user_create.username}: {e}")
        raise


async def get_user_by_username(session: AsyncSession, username: str) -> UserResponse | None:
    """
    Получает пользователя по имени.

    :param session: Асинхронная сессия БД.
    :type session: AsyncSession
    :param username: Имя пользователя.
    :type username: str
    :returns: Найденная запись пользователя или None, если не найдена.
    :rtype: UserResponse | None
    """
    try:
        result = await session.execute(select(User).where(User.username == username))
        user = result.scalars().first()
        if user:
            logger.debug(f"Retrieved user: {username}")
            return UserResponse.model_validate(user)
        logger.debug(f"No user found with username: {username}")
        return None
    except Exception as e:
        logger.error(f"Error retrieving user {username}: {e}")
        raise
