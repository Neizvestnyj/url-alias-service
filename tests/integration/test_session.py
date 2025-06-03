from asyncpg.exceptions import ConnectionDoesNotExistError, InvalidPasswordError
import pytest

from app.core.config import settings
from app.db.session import DatabaseManager


@pytest.mark.anyio
async def test_connect_success() -> None:
    """
    Тест успешного подключения к тестовой БД.

    Ожидается, что DatabaseManager сможет успешно установить соединение
    с указанной тестовой БД без выброса исключений.
    """
    db = DatabaseManager(settings.SQLALCHEMY_TEST_DATABASE_URL)
    try:
        await db.connect()
    finally:
        await db.close()


@pytest.mark.anyio
async def test_connect_invalid_url() -> None:
    """
    Тест ошибки подключения с некорректным URL.

    При попытке соединения с заведомо неправильной строкой подключения
    должно быть выброшено исключение ConnectionDoesNotExistError.
    """
    db = DatabaseManager("postgresql+asyncpg://wrong:wrong@localhost:5432/invalid")
    with pytest.raises((ConnectionDoesNotExistError, InvalidPasswordError)):
        await db.connect()
