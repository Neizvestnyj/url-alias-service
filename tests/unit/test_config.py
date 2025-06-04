from app.core.config import settings


def test_database_url_sync_replaces_driver() -> None:
    """Unit test: Проверяет, что свойство DATABASE_URL_SYNCзаменяет 'asyncpg' на 'psycopg2' в строке подключения."""
    async_url = settings.DATABASE_URL
    sync_url = settings.DATABASE_URL_SYNC

    assert "asyncpg" in async_url
    assert "psycopg2" in sync_url
    assert sync_url == async_url.replace("asyncpg", "psycopg2")
