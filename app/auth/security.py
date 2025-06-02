from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.utils import verify_password
from app.core.logging import logger
from app.db.crud.user import get_user_by_username
from app.db.session import get_session
from app.schemas.user import UserResponse

# Настройка Basic Auth
security = HTTPBasic()

credentials_depends = Depends(security)
session_depends = Depends(get_session)


async def get_current_user(
    credentials: HTTPBasicCredentials = credentials_depends, session: AsyncSession = session_depends
) -> UserResponse:
    """
    Проверяет учетные данные Basic Auth и возвращает текущего пользователя.

    :param credentials: Учетные данные Basic Auth (имя пользователя и пароль).
    :type credentials: HTTPBasicCredentials
    :param session: Асинхронная сессия базы данных.
    :type session: AsyncSession
    :returns: Данные текущего пользователя.
    :rtype: UserResponse
    :raises HTTPException: Если пользователь не найден или пароль неверный.
    """
    try:
        username = credentials.username
        user: UserResponse = await get_user_by_username(session, username)
        if not user:
            logger.warning(f"Authentication failed: User {username} not found")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
                headers={"WWW-Authenticate": "Basic"},
            )
        if not verify_password(credentials.password, user.hashed_password):
            logger.warning(f"Authentication failed: Invalid password for user {username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
                headers={"WWW-Authenticate": "Basic"},
            )

        logger.debug(f"Authenticated user: {username}")
        return user
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error authenticating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        ) from None
