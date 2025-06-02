from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.logging import logger
from app.db.session import db_manager


@asynccontextmanager
async def app_lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Управляет жизненным циклом приложения.

    :param app: FastAPI приложение.
    :type app: FastAPI
    :returns: Асинхронный генератор для управления жизненным циклом.
    :rtype: AsyncGenerator[None, None]
    """
    logger.info("Application startup...")
    await db_manager.connect()
    logger.info("Database connected.")

    yield

    logger.info("Application shutdown...")
    await db_manager.close()
    logger.info("Database disconnected.")
