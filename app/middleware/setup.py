from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.logging import logger


def configure_middleware(app: FastAPI) -> None:
    """
    Настраивает middleware для приложения FastAPI :param app: Приложение.

    :param app: FastAPI
    :returns: None
    """
    logger.info("Configuring middleware...")

    # Настройка CORS
    app.add_middleware(
        middleware_class=CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["*"],
    )

    logger.info("Middleware configuration complete")
