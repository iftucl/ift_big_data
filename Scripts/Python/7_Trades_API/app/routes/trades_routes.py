from fastapi import APIRouter, Depends, status, Path
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from typing import Annotated

from modules.utils.local_logger import lambro_logger
from app.api_models.api_requests.trades_requests import AllTradesRequest, TraderTradesRequest
from app.api_models.api_responses.trade_model import Trade
from app.modules.mongodb_trades_get import TradeQuery

router = APIRouter()

@router.get("/trades", summary="Gets all trades", description="Returns a full list of trades")
async def get_all_trades_endpoint(input_data: AllTradesRequest = Depends()) -> list[Trade]:
    lambro_logger.info(f"Executing request query to get all trades in TradingRecord collection")
    mongo_trades = TradeQuery(database="Trades", collection="TradingRecord")
    trades_output = mongo_trades.get_trades(limit=input_data.limit)
    if not trades_output:
        return JSONResponse(status_code=status.HTTP_200_OK, content=[])
    return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(trades_output))

@router.get("/trades/{trader_id}", summary="Gets all trades", description="Returns a full list of trades")
async def get_trader_trades_endpoint(trader_id: Annotated[str, Path(description="Get all trades by trader", title="Trader Trades", example="SML1458")],
                                     input_data: TraderTradesRequest = Depends()) -> list[Trade]:
    lambro_logger.info(f"Executing request query to get {trader_id} trades in TradingRecord collection")
    mongo_trades = TradeQuery(database="Trades", collection="TradingRecord")
    trades_output = mongo_trades.get_trades(limit=input_data.limit, match=trader_id)
    if not trades_output:
        return JSONResponse(status_code=status.HTTP_200_OK, content=[])
    return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(trades_output))

