import logging

from httpx import AsyncClient
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from tests.utils.db_mocks import create_test_url, create_test_user


async def test_log_request_middleware(
    client: AsyncClient, async_session: AsyncSession, caplog: pytest.LogCaptureFixture
) -> None:
    """
    Тестирует middleware логирования запросов и ответов.

    :param client: Асинхронный клиент FastAPI.
    :type client: AsyncClient
    :param async_session: Асинхронная сессия SQLAlchemy.
    :type async_session: AsyncSession
    :param caplog: Фикстура для захвата логов.
    :type caplog: pytest.LogCaptureFixture
    :returns: None
    """
    caplog.set_level(logging.INFO, logger="url_alias_service")

    # Создаём тестовый URL
    user = await create_test_user(async_session, username="testuser")
    await create_test_url(async_session, user_id=user["id"], original_url="https://example.com", short_key="testurl")

    # Отправляем запрос
    response = await client.get("api/v1/r/testurl", follow_redirects=False)
    assert response.status_code == 307, f"Expected 307, got {response.status_code}: {response.text}"

    # Проверяем логи
    log_records = [record.message for record in caplog.records]
    assert any("Incoming request: GET http://test/api/v1/r/testurl" in msg for msg in log_records), (
        "Request log not found"
    )
    assert any("Response status: 307" in msg for msg in log_records), "Response status log not found"
