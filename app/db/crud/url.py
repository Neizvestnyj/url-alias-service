from sqlalchemy import delete, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.logging import logger
from app.db.models import URL
from app.schemas.url import URLCreate, URLResponse


async def create_url(session: AsyncSession, url_create: URLCreate, user_id: int) -> URLResponse:
    """
    Создаёт новую короткую ссылку в базе данных.

    :param session: Асинхронная сессия базы данных.
    :type session: AsyncSession
    :param url_create: Данные для создания ссылки.
    :type url_create: URLCreate
    :param user_id: Идентификатор пользователя, создавшего ссылку.
    :type user_id: int
    :returns: Созданная запись URL.
    :rtype: URLResponse
    """
    try:
        db_url = URL(**url_create.model_dump(), user_id=user_id)
        session.add(db_url)
        await session.commit()
        await session.refresh(db_url)

        return URLResponse.model_validate(db_url)
    except Exception as e:
        logger.error(f"Error creating URL for user_id {user_id}: {e}")
        raise


async def get_url_by_short_key(session: AsyncSession, short_key: str) -> URLResponse | None:
    """
    Получает URL по короткому ключу.

    :param session: Асинхронная сессия базы данных.
    :type session: AsyncSession
    :param short_key: Короткий ключ ссылки.
    :type short_key: str
    :returns: Найденная запись URL или None, если не найдена.
    :rtype: UserResponse | None
    """
    try:
        result = await session.execute(select(URL).where(URL.short_key == short_key))
        url = result.scalars().first()
        if url:
            return URLResponse.model_validate(url)
        return None
    except Exception as e:
        logger.error(f"Error retrieving URL by short_key {short_key}: {e}")
        raise


async def get_url_by_id(session: AsyncSession, url_id: int) -> URLResponse | None:
    """
    Получает URL по идентификатору.

    :param session: Асинхронная сессия базы данных.
    :type session: AsyncSession
    :param url_id: Идентификатор URL.
    :type url_id: int
    :returns: Найденная запись URL или None, если не найдена.
    :rtype: Optional[URLResponse]
    """
    try:
        result = await session.execute(select(URL).where(URL.id == url_id))
        url = result.scalars().first()
        if url:
            return URLResponse.model_validate(url)
        return None
    except Exception as e:
        logger.error(f"Error retrieving URL by id {url_id}: {e}")
        raise e from None


async def get_urls_by_user(
    session: AsyncSession, user_id: int, page: int, per_page: int, is_active: bool | None = None
) -> tuple[list[URLResponse], int]:
    """
    Получает список URL пользователя с пагинацией и фильтрацией.

    :param session: Асинхронная сессия базы данных.
    :type session: AsyncSession
    :param user_id: Идентификатор пользователя.
    :type user_id: int
    :param page: Номер страницы (начинается с 1).
    :type page: int
    :param per_page: Количество записей на страницу.
    :type per_page: int
    :param is_active: Фильтр по активным ссылкам (True/False или None для всех).
    :type is_active: bool | None
    :returns: Кортеж из списка URL и общего количества записей.
    :rtype: Tuple[List[URL], int]
    :raises Exception: Если произошла ошибка при запросе к базе данных.
    """
    try:
        offset = (page - 1) * per_page
        query = select(URL).where(URL.user_id == user_id)
        total_query = select(func.count()).select_from(URL).where(URL.user_id == user_id)

        if is_active is not None:
            query = query.where(URL.is_active == is_active)
            total_query = total_query.where(URL.is_active == is_active)

        query = query.order_by(URL.created_at.desc()).limit(per_page).offset(offset)

        result = await session.execute(query)
        urls = result.scalars().all()
        urls = [URLResponse.model_validate(url) for url in urls]
        total_result = await session.execute(total_query)
        total = total_result.scalar_one()

        return urls, total
    except Exception as e:
        logger.error(f"Error retrieving URLs for user_id {user_id}: {e}")
        raise


async def increment_click_count(session: AsyncSession, url_id: int) -> None:
    """
    Увеличивает счётчик кликов для URL.

    :param session: Асинхронная сессия базы данных.
    :type session: AsyncSession
    :param url_id: Идентификатор URL.
    :type url_id: int
    :returns: None
    """
    try:
        await session.execute(update(URL).where(URL.id == url_id).values(click_count=URL.click_count + 1))
        await session.commit()
    except Exception as e:
        logger.error(f"Error incrementing click count for URL id {url_id}: {e}")
        raise


async def delete_url(session: AsyncSession, url_id: int) -> bool:
    """
    Удаляет URL по идентификатору.

    :param session: Асинхронная сессия базы данных.
    :type session: AsyncSession
    :param url_id: Идентификатор URL.
    :type url_id: int
    :returns: True если удаление успешно, False если URL не найден.
    :rtype: bool
    """
    try:
        result = await session.execute(delete(URL).where(URL.id == url_id))
        await session.commit()
        rowcount = result.rowcount
        if rowcount > 0:
            return True
        return False
    except Exception as e:
        logger.error(f"Error deleting URL with id {url_id}: {e}")
        raise
