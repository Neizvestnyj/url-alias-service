from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.security import get_current_user
from app.core.logging import logger
from app.db.session import get_session
from app.schemas.url import URLCreate, URLResponse
from app.schemas.user import UserResponse
from app.services.url_service import create_short_url as create_short_url_service, delete_user_url, get_user_urls

router = APIRouter(
    prefix="/urls",
    tags=["URLs"],
)

current_user_depends = Depends(get_current_user)
session_depends = Depends(get_session)


@router.post("", response_model=URLResponse, status_code=status.HTTP_201_CREATED)
async def create_short_url(
    url_create: URLCreate, current_user: UserResponse = current_user_depends, session: AsyncSession = session_depends
) -> URLResponse:
    """
    Создаёт новую короткую ссылку.

    :param url_create: Данные для создания ссылки.
    :type url_create: URLCreate
    :param current_user: Текущий аутентифицированный пользователь.
    :type current_user: UserResponse
    :param session: Асинхронная сессия базы данных.
    :type session: AsyncSession
    :returns: Созданная запись URL.
    :rtype: URLResponse
    :raises HTTPException: Если создание не удалось.
    """
    try:
        url = await create_short_url_service(
            session,
            original_url=url_create.original_url,
            short_key=url_create.short_key,
            user_id=current_user.id,
        )
        logger.info(f"User {current_user.username} created URL with short_key {url.short_key}")
        return url
    except ValueError as e:
        logger.warning(f"Create URL failed: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from None
    except Exception as e:
        logger.error(f"Error creating URL for user {current_user.username}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create URL") from None


@router.get("", response_model=list[URLResponse])
async def get_user_urls_endpoint(
    current_user: UserResponse = current_user_depends, session: AsyncSession = session_depends
) -> list[URLResponse]:
    """
    Получает список URL, созданных пользователем.

    :param current_user: Текущий аутентифицированный пользователь.
    :type current_user: UserResponse
    :param session: Асинхронная сессия базы данных.
    :type session: AsyncSession
    :returns: Список URL записей.
    :rtype: list[URLResponse]
    """
    try:
        urls = await get_user_urls(session, current_user.id)
        logger.info(f"Retrieved {len(urls)} URLs for user {current_user.username}")
        return urls
    except Exception as e:
        logger.error(f"Error retrieving URLs for user {current_user.username}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve URLs"
        ) from None


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_short_url(
    url_id: int, current_user: UserResponse = current_user_depends, session: AsyncSession = session_depends
) -> None:
    """
    Удаляет URL по идентификатору.

    :param url_id: Идентификатор URL.
    :type url_id: int
    :param current_user: Текущий аутентифицированный пользователь.
    :type current_user: UserResponse
    :param session: Асинхронная сессия базы данных.
    :type session: AsyncSession
    :returns: None
    :raises HTTPException: Если URL не найден или не принадлежит пользователю.
    """
    try:
        await delete_user_url(session, url_id, current_user.id)
        logger.info(f"User {current_user.username} deleted URL with id {url_id}")
    except ValueError as e:
        logger.warning(f"Delete failed: {str(e)}")
        if str(e) == "URL not found":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from None
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from None
    except Exception as e:
        logger.error(f"Error deleting URL id {url_id} for user {current_user.username}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete URL") from None
