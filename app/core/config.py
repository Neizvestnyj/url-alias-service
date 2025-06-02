from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.logging import logger, update_logging

BASE_DIR = Path(__file__).resolve().parents[2]
ENV_PATH = BASE_DIR / ".env"


class Settings(BaseSettings):
    """
    Настройки приложения.

    :param APP_TITLE: Название приложения.
    :type APP_TITLE: str
    :param DATABASE_URL: URL для подключения к PostgreSQL.
    :type DATABASE_URL: str
    :param SQLALCHEMY_TEST_DATABASE_URL: URL для подключения к тестовой базе PostgreSQL.
    :type SQLALCHEMY_TEST_DATABASE_URL: str
    :param ENVIRONMENT: Окружение приложения (development, production).
    :type ENVIRONMENT: str
    """

    APP_TITLE: str = "URL Alias Service"
    DATABASE_URL: str = "postgresql+asyncpg://postgres:1234@localhost:5432/url_alias_db"
    SQLALCHEMY_TEST_DATABASE_URL: str = "postgresql+asyncpg://postgres:1234@localhost:5432/test_url_alias_db"
    ENVIRONMENT: str = "development"

    model_config = SettingsConfigDict(
        env_file=str(ENV_PATH),
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    @property
    def DATABASE_URL_SYNC(self) -> str:
        """
        Возвращает синхронный URL подключения к базе данных, заменяя драйвер ``asyncpg`` на ``psycopg2``.

        :returns: URL базы данных для синхронного SQLAlchemy (например, для Alembic).
        :rtype: str
        """
        return self.DATABASE_URL.replace("asyncpg", "psycopg2")


settings = Settings()
update_logging(environment=settings.ENVIRONMENT)
logger.info(f"Application settings loaded: APP_TITLE={settings.APP_TITLE}, ENVIRONMENT={settings.ENVIRONMENT}")
