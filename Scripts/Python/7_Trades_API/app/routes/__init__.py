from fastapi import APIRouter
from app.routes.trades_routes import router as trades_router


router = APIRouter()
router.include_router(trades_router, prefix="/trades", tags=["trades"])