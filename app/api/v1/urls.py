from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.security import get_current_user
from app.core.logging import logger
from app.db.session import get_session
from app.schemas.url import URLCreate, URLListResponse, URLResponse
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
        return url
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from None
    except Exception as e:
        logger.error(f"Error creating URL for user {current_user.username}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create URL") from None


@router.get("", response_model=URLListResponse)
async def get_user_urls_endpoint(
    page: int = Query(1, ge=1, description="Номер страницы"),
    per_page: int = Query(10, ge=1, le=100, description="Количество записей на страницу"),
    is_active: bool | None = None,
    current_user: UserResponse = current_user_depends,
    session: AsyncSession = session_depends,
) -> URLListResponse:
    """
    Получает список URL, созданных пользователем, с пагинацией и фильтрацией.

    :param page: Номер страницы (начинается с 1).
    :type page: int
    :param per_page: Количество записей на страницу (максимум 100).
    :type per_page: int
    :param is_active: Фильтр по активным ссылкам (True/False или None для всех).
    :type is_active: bool | None
    :param current_user: Текущий аутентифицированный пользователь.
    :type current_user: UserResponse
    :param session: Асинхронная сессия базы данных.
    :type session: AsyncSession
    :returns: Список URL с метаинформацией пагинации.
    :rtype: URLListResponse
    :raises HTTPException: Если произошла ошибка при получении данных.
    """
    try:
        urls, total = await get_user_urls(
            session, user_id=current_user.id, page=page, per_page=per_page, is_active=is_active
        )
        return URLListResponse(
            items=[URLResponse.model_validate(url) for url in urls],
            total=total,
            page=page,
            per_page=per_page,
            total_pages=(total + per_page - 1) // per_page,
        )
    except Exception as e:
        logger.error(f"Error retrieving URLs for user {current_user.username}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve URLs"
        ) from None


@router.delete("/{url_id}", status_code=status.HTTP_204_NO_CONTENT)
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
    except ValueError as e:
        if str(e) == "URL not found":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from None
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e)) from None
    except Exception as e:
        logger.error(f"Error deleting URL id {url_id} for user {current_user.username}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error") from None
