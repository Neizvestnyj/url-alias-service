from fastapi import APIRouter

from app.api.v1 import auth, redirect, urls

api_v1_router = APIRouter(prefix="/api/v1")

api_v1_router.include_router(auth.router)
api_v1_router.include_router(redirect.router)
api_v1_router.include_router(urls.router)
