from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.db.session import get_session
from app.services.url_service import redirect_to_url

router = APIRouter(prefix="/r", tags=["Redirect"])
session_depends = Depends(get_session)


@router.get("/{short_key}", response_class=RedirectResponse)
async def redirect_to_url_endpoint(short_key: str, session: AsyncSession = session_depends) -> RedirectResponse:
    """
    Перенаправляет на оригинальный URL по короткому ключу.

    :param short_key: Короткий ключ ссылки.
    :type short_key: str
    :param session: Асинхронная сессия базы данных.
    :type session: AsyncSession
    :returns: Перенаправление на оригинальный URL.
    :rtype: RedirectResponse
    :raises HTTPException: Если ссылка не найдена, неактивна или истёк срок действия.
    """
    try:
        original_url = await redirect_to_url(session, short_key)
        return RedirectResponse(url=str(original_url), status_code=status.HTTP_307_TEMPORARY_REDIRECT)
    except ValueError as e:
        if str(e) == "URL not found":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from None
        raise HTTPException(status_code=status.HTTP_410_GONE, detail=str(e)) from None
    except Exception as e:
        logger.error(f"Error redirecting for short_key {short_key}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error") from None
