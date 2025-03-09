from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder

from modules.utils.local_logger import lambro_logger
from app.api_models.api_requests.trades_requests import AllTradesRequest
from app.api_models.api_responses.trade_model import Trade
from app.modules.mongodb_trades_get import TradeQuery

router = APIRouter()

@router.get("/trades", summary="Gets all trades", description="Returns a full list of trades")
async def get_all_trades_endpoint(input_data: AllTradesRequest = Depends()) -> list[Trade]:
    lambro_logger.info(f"Executing request query to get all trades in TradingRecord collection")
    mongo_trades = TradeQuery(database="Trades", collection="TradingRecord")
    trades_output = mongo_trades.get_trades(limit=10)
    if not trades_output:
        return JSONResponse(status_code=status.HTTP_200_OK, content=[])
    return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(trades_output))

