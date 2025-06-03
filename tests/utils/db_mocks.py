import base64
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.crud.user import create_user
from app.db.models import URL
from app.schemas.url import URLResponse
from app.schemas.user import UserCreate


async def create_test_user(session: AsyncSession, username: str = "testuser", password: str = "testpass") -> dict:
    """
    Создаёт тестового пользователя в базе данных.

    :param session: Асинхронная сессия SQLAlchemy.
    :type session: AsyncSession
    :param username: Имя пользователя.
    :type username: str
    :param password: Пароль пользователя.
    :type password: str
    :returns: Данные созданного пользователя.
    :rtype: Dict
    """
    user_create = UserCreate(username=username, password=password)
    user = await create_user(session, user_create)
    return {"id": user.id, "username": user.username}


async def get_headers_and_user_id(
    async_session: AsyncSession, username: str = "testuser", password: str = "testpass"
) -> tuple[dict[str, str], int]:
    """
    Создаёт заголовки с Basic Auth для тестов.

    :param async_session: Асинхронная сессия SQLAlchemy.
    :type async_session: AsyncSession
    :param username: Имя пользователя.
    :type username: str
    :param password: Пароль пользователя.
    :type password: str
    :returns: Заголовки с авторизацией.
    :rtype: dict
    """
    user = await create_test_user(async_session, username=username, password=password)
    credentials = base64.b64encode(b"testuser:testpass").decode("utf-8")
    return {"Authorization": f"Basic {credentials}"}, user["id"]


async def create_test_url(
    session: AsyncSession,
    user_id: int,
    original_url: str = "https://example.com",
    short_key: str = "exmpl",
    is_active: bool = True,
    expires_at: datetime | None = None,
) -> URLResponse:
    """
    Создаёт тестовую короткую ссылку в базе данных.

    :param session: Асинхронная сессия SQLAlchemy.
    :type session: AsyncSession
    :param user_id: Идентификатор пользователя.
    :type user_id: int
    :param original_url: Исходный URL.
    :type original_url: str
    :param short_key: Короткий ключ.
    :type short_key: str
    :param is_active: Статус активности ссылки.
    :type is_active: bool
    :param expires_at: Время истечения ссылки.
    :type expires_at: datetime | None
    :returns: Созданная запись URL.
    :rtype: URLResponse
    """
    if expires_at is None:
        expires_at = datetime.now(UTC) + timedelta(days=1)
    url = URL(
        original_url=original_url,
        short_key=short_key,
        user_id=user_id,
        is_active=is_active,
        expires_at=expires_at,
        click_count=0,
    )
    session.add(url)
    await session.commit()
    await session.refresh(url)
    return URLResponse.model_validate(url)
