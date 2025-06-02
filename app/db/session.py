from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import sqlalchemy
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.logging import logger
from app.db.models import Base


class DatabaseManager:
    """Базовый класс для управления подключением к базе данных."""

    def __init__(self, url: str | None = None) -> None:
        """
        Инициализирует подключение к базе данных PostgreSQL.

        :param url: Url БД
        """
        if not url:
            url = settings.DATABASE_URL

        self.engine = create_async_engine(
            url,
            echo=False,
            pool_size=25,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=1800,  # Время жизни соединения в пуле перед пересозданием (сек)
            isolation_level="READ COMMITTED",
        )
        self.async_session = sessionmaker(self.engine, expire_on_commit=False, class_=AsyncSession)

    async def connect(self) -> None:
        """Проверяет подключение к базе данных и создаёт таблицы, если они не существуют."""
        try:
            async with self.engine.connect() as conn:
                # Проверяем, существуют ли таблицы
                existing_tables = await conn.run_sync(lambda sync_conn: sync_conn.dialect.get_table_names(sync_conn))
                if not existing_tables:
                    await conn.run_sync(Base.metadata.create_all)
                    logger.info("Database tables created")
                else:
                    logger.info("Database tables already exist")
            logger.info("Successfully connected to PostgreSQL")
        except sqlalchemy.exc.OperationalError as e:
            logger.error(f"Database connection error: {type(e).__name__}: {str(e)}")
            raise

    async def close(self) -> None:
        """Закрывает все соединения с базой данных."""
        await self.engine.dispose()
        logger.info("Database connections closed")

    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """
        Асинхронный контекстный менеджер для сессии базы данных.

        Откатывает транзакцию при ошибке и автоматически закрывает сессию.
        """
        async with self.async_session() as session:
            try:
                logger.debug("Opening new database session")
                yield session
                logger.debug("Session ready to commit or rollback")
            except Exception as e:
                await session.rollback()
                logger.error(f"Database error: {e}")
                raise
            finally:
                await session.close()
                logger.debug("Session closed")


# Глобальный экземпляр DatabaseManager
db_manager = DatabaseManager()


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Предоставляет асинхронную сессию базы данных для зависимостей FastAPI.

    :returns: Асинхронная сессия SQLAlchemy.
    :rtype: AsyncGenerator[AsyncSession, None]
    """
    async with db_manager.session() as session:
        yield session


if __name__ == "__main__":
    import asyncio

    async def initialize() -> None:
        """Инициализация базы данных."""
        await db_manager.connect()

    asyncio.run(initialize())
