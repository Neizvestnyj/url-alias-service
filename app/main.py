from fastapi import FastAPI

from app.api.v1 import auth, redirect, urls
from app.core.config import settings
from app.core.logging import logger
from app.lifecycle.lifespan_events import app_lifespan
from app.middleware.setup import configure_middleware

# Создание FastAPI-приложения
app = FastAPI(
    title=settings.APP_TITLE,
    lifespan=app_lifespan,
)

# Настройка middleware (включая CORS)
configure_middleware(app)

# Подключение роутеров
app.include_router(auth.router)
app.include_router(redirect.router)
app.include_router(urls.router)

if __name__ == "__main__":
    import uvicorn

    logger.info("Starting Uvicorn server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
