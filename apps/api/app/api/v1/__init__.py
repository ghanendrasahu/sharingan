"""API v1 router."""

from fastapi import APIRouter

from app.api.v1.analysis import router as analysis_router
from app.api.v1.auth import router as auth_router
from app.api.v1.documents import router as documents_router
from app.api.v1.organizations import router as organizations_router
from app.api.v1.payments import router as payments_router
from app.api.v1.reports import router as reports_router
from app.api.v1.search import router as search_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(organizations_router)
api_router.include_router(documents_router)
api_router.include_router(analysis_router)
api_router.include_router(search_router)
api_router.include_router(reports_router)
api_router.include_router(payments_router)
