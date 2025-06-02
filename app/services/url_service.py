from datetime import UTC, datetime
import random
import string

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.db.crud.url import (
    create_url,
    delete_url,
    get_url_by_id,
    get_url_by_short_key,
    get_urls_by_user,
    increment_click_count,
)
from app.schemas.url import URLCreate, URLResponse


def generate_short_key(length: int = 6) -> str:
    """
    Генерирует случайный короткий ключ.

    :param length: Длина ключа.
    :type length: int
    :returns: Случайный короткий ключ.
    :rtype: str
    """
    characters = string.ascii_letters + string.digits
    return "".join(random.choice(characters) for _ in range(length))


async def create_short_url(
    session: AsyncSession,
    original_url: str,
    short_key: str | None,
    user_id: int,
) -> URLResponse:
    """
    Создаёт новую короткую ссылку.

    :param session: Асинхронная сессия базы данных.
    :type session: AsyncSession
    :param original_url: Исходный URL.
    :type original_url: str
    :param short_key: Пользовательский короткий ключ (опционально).
    :type short_key: Optional[str]
    :param user_id: Идентификатор пользователя.
    :type user_id: int
    :returns: Созданная запись URL.
    :rtype: URLResponse
    :raises ValueError: Если короткий ключ уже существует.
    """
    try:
        if short_key:
            existing_url = await get_url_by_short_key(session, short_key)
            if existing_url:
                logger.warning(f"Short key {short_key} already exists")
                raise ValueError("Short key already exists")
        else:
            for _ in range(5):  # Пробуем 5 раз сгенерировать уникальный ключ
                short_key = generate_short_key()
                existing_url = await get_url_by_short_key(session, short_key)
                if not existing_url:
                    break
            else:
                logger.error("Failed to generate unique short key after 5 attempts")
                raise ValueError("Unable to generate unique short key")

        url_create = URLCreate(original_url=original_url, short_key=short_key)
        url = await create_url(session, url_create, user_id)
        logger.info(f"Created short URL {url.short_key} for user_id {user_id}")
        return url
    except ValueError as e:
        logger.error(f"Error creating short URL for user_id {user_id}: {e}")
        raise
    except Exception as e:
        logger.error(f"Error creating short URL for user_id {user_id}: {e}")
        raise e from None


async def get_user_urls(session: AsyncSession, user_id: int) -> list[URLResponse]:
    """
    Получает список URL пользователя.

    :param session: Асинхронная сессия базы данных.
    :type session: AsyncSession
    :param user_id: Идентификатор пользователя.
    :type user_id: int
    :returns: Список URL записей.
    :rtype: List[URLResponse]
    """
    try:
        urls = await get_urls_by_user(session, user_id)
        logger.debug(f"Retrieved {len(urls)} URLs for user_id {user_id}")
        return urls
    except Exception as e:
        logger.error(f"Error retrieving URLs for user_id {user_id}: {e}")
        raise e from None


async def delete_user_url(session: AsyncSession, url_id: int, user_id: int) -> None:
    """
    Удаляет URL, если он принадлежит пользователю.

    :param session: Асинхронная сессия базы данных.
    :type session: AsyncSession
    :param url_id: Идентификатор URL.
    :type url_id: int
    :param user_id: Идентификатор пользователя.
    :type user_id: int
    :returns: None
    :raises ValueError: Если URL не найден или не принадлежит пользователю.
    """
    try:
        url = await get_url_by_id(session, url_id)
        if not url:
            logger.warning(f"Delete failed: No URL found with id {url_id}")
            raise ValueError("URL not found")
        if url.user_id != user_id:
            logger.warning(f"User {user_id} attempted to delete URL id {url_id} not owned")
            raise ValueError("Not authorized to delete this URL")

        success = await delete_url(session, url_id)
        if not success:
            logger.warning(f"Delete failed: No URL found with id {url_id}")
            raise ValueError("URL not found")

        logger.info(f"Deleted URL id {url_id} for user_id {user_id}")
    except ValueError as e:
        raise
    except Exception as e:
        logger.error(f"Error deleting URL id {url_id} for user_id {user_id}: {e}")
        raise e from None


async def redirect_to_url(session: AsyncSession, short_key: str) -> str:
    """
    Получает оригинальный URL для перенаправления и увеличивает счётчик кликов.

    :param session: Асинхронная сессия базы данных.
    :type session: AsyncSession
    :param short_key: Короткий ключ ссылки.
    :type short_key: str
    :returns: Оригинальный URL.
    :rtype: str
    :raises ValueError: Если ссылка не найдена, неактивна или истёк срок действия.
    """
    try:
        url = await get_url_by_short_key(session, short_key)
        if not url:
            logger.warning(f"Redirect failed: No URL found with short_key {short_key}")
            raise ValueError("URL not found")
        if not url.is_active:
            logger.warning(f"Redirect failed: URL with short_key {short_key} is inactive")
            raise ValueError("URL is inactive")
        if url.expires_at < datetime.now(UTC):
            logger.warning(f"Redirect failed: URL with short_key {short_key} has expired")
            raise ValueError("URL has expired")

        await increment_click_count(session, url.id)
        logger.info(f"Redirecting to {url.original_url} for short_key {short_key}")
        return url.original_url
    except ValueError as e:
        logger.error(f"Error redirecting for short_key {short_key}: {e}")
        raise
    except Exception as e:
        logger.error(f"Error redirecting for short_key {short_key}: {e}")
        raise e from None
