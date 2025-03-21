from fastapi import APIRouter
from app.routes.trades_routes import router as trades_router
from app.routes.traders_info import router as traders_router
from app.routes.trades_streaming import router as stream_trades
router = APIRouter()
router.include_router(trades_router, prefix="/trades", tags=["trades"])
router.include_router(traders_router, prefix="/traders", tags=["traders"])
router.include_router(stream_trades, prefix="/traders", tags=["traders"])