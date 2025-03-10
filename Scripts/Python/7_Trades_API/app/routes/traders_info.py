from fastapi import APIRouter, Depends, status, Path
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from typing import Annotated

from modules.utils.local_logger import lambro_logger
from app.modules.postgres_get_trades import get_unique_trader_ids

router = APIRouter()

@router.get("/ids", summary="Gets all trader idss", description="Returns a full list of traders ids")
async def get_all_traderids_endpoint() -> list[str]:
    lambro_logger.info(f"Request query to get all trader ids  - start")
    traders_ids = await get_unique_trader_ids(database="fift")
    lambro_logger.info(f"Executing request query to get all trades in TradingRecord collection - completed")
    if not traders_ids:
        return JSONResponse(status_code=status.HTTP_200_OK, content=[])
    return JSONResponse(status_code=status.HTTP_200_OK, content=traders_ids)
