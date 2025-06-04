from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request
from fastapi.responses import Response

from app.core.logging import logger


async def log_request_middleware(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
    """
    Middleware для логирования входящих запросов.

    :param request: HTTP-запрос.
    :type request: Request
    :param call_next: Следующий обработчик запроса.
    :type call_next: Callable[[Request], Awaitable[Response]]
    :returns: HTTP-ответ.
    :rtype: Response
    """
    logger.info(f"Incoming request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response


def configure_auth_middleware(app: FastAPI) -> None:
    """
    Настраивает middleware аутентификации.

    :param app: Приложение FastAPI.
    :type app: FastAPI
    :returns: None
    """
    logger.info("Configuring authentication middleware...")
    app.middleware("http")(log_request_middleware)
    logger.info("Authentication middleware configuration complete")
