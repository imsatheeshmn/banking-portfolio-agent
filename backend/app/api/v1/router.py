"""V1 API Router combining all sub-routers."""

from fastapi import APIRouter

from app.api.v1.customers import router as customers_router
from app.api.v1.portfolios import router as portfolios_router
from app.api.v1.positions import router as positions_router
from app.api.v1.securities import router as securities_router
from app.api.v1.transactions import router as transactions_router

api_router = APIRouter()
api_router.include_router(customers_router)
api_router.include_router(portfolios_router)
api_router.include_router(securities_router)
api_router.include_router(transactions_router)
api_router.include_router(positions_router)
