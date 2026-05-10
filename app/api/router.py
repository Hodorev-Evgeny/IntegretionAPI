from fastapi import APIRouter

from app.api.exchange import router as exchange_router


api_router = APIRouter()

api_router.include_router(exchange_router)