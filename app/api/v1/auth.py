from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.db.session import get_session
from app.schemas.user import UserCreate, UserResponse
from app.services.user_service import create_new_user

router = APIRouter(
    prefix="/auth",
    tags=["Auth"],
)

session_depends = Depends(get_session)


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user_create: UserCreate, session: AsyncSession = session_depends) -> UserResponse:
    """
    Регистрирует нового пользователя.

    :param user_create: Данные для создания пользователя.
    :type user_create: UserCreate
    :param session: Асинхронная сессия базы данных.
    :type session: AsyncSession
    :returns: Созданная запись пользователя.
    :rtype: UserResponse
    :raises HTTPException: Если регистрация не удалась.
    """
    try:
        user = await create_new_user(session, user_create)
        logger.info(f"Registered user {user.username}")
        return user
    except ValueError as e:
        logger.warning(f"Registration failed: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from None
    except Exception as e:
        logger.error(f"Error registering user {user_create.username}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to register user"
        ) from None
