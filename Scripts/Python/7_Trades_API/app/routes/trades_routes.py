from fastapi import APIRouter, Depends, status, Path
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from typing import Annotated

from modules.utils.local_logger import lambro_logger
from app.api_models.api_requests.trades_requests import AllTradesRequest, TraderTradesRequest, CreateTrade, DeleteTradeRequest
from app.api_models.api_responses.trade_model import Trade
from app.modules.mongodb_trades_get import TradeQuery, TradeInsert, TradeDelete

router = APIRouter()

@router.get("/trades", summary="Gets all trades", description="Returns a full list of trades")
async def get_all_trades_endpoint(input_data: AllTradesRequest = Depends()) -> list[Trade]:
    lambro_logger.info(f"Executing request query to get all trades in TradingRecord collection - start")
    mongo_trades = TradeQuery(database="Trades", collection="TradingRecord")
    trades_output = mongo_trades.get_trades(limit=input_data.limit)
    lambro_logger.info(f"Executing request query to get all trades in TradingRecord collection - completed")
    if not trades_output:
        return JSONResponse(status_code=status.HTTP_200_OK, content=[])
    return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(trades_output))

@router.get("/trades/{trader_id}", summary="Gets all trades", description="Returns a full list of trades")
async def get_trader_trades_endpoint(trader_id: Annotated[str, Path(description="Get all trades by trader", title="Trader Trades", example="SML1458")],
                                     input_data: TraderTradesRequest = Depends()) -> list[Trade]:
    lambro_logger.info(f"Executing request query to get {trader_id} trades in TradingRecord collection - start")
    mongo_trades = TradeQuery(database="Trades", collection="TradingRecord")
    trades_output = mongo_trades.get_trades(limit=input_data.limit, match=trader_id)
    lambro_logger.info(f"Executing request query to get {trader_id} trades in TradingRecord collection - completed")
    if not trades_output:
        return JSONResponse(status_code=status.HTTP_200_OK, content=[])    
    return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(trades_output))

@router.post("/trades/{trader_id}", summary="Create a new trade", description="For a trader, creates a new trade")
async def post_trader_trade_endpoint(trader_id: Annotated[str, Path(description="Get all trades by trader", title="Trader Trades", example="SML1458")],
                                     input_data: CreateTrade = Depends()) -> list[Trade]:
    lambro_logger.info(f"Executing request query to crate a new trade for {trader_id} TradingRecord collection - start")
    insert_trades = TradeInsert(database="Trades", collection="TradingRecord")
    lambro_logger.info(f"Executing request query to crate a new trade for {trader_id} TradingRecord collection - completed")
    trades_output = insert_trades.insert_trade(input_data)
    if not trades_output:
        return JSONResponse(status_code=status.HTTP_200_OK, content=[])
    return JSONResponse(status_code=status.HTTP_201_CREATED, content="Created")

@router.delete("/trades/{trader_id}", summary="Create a new trade", description="For a trader, creates a new trade")
async def post_trader_trade_endpoint(trader_id: Annotated[str, Path(description="Get all trades by trader", title="Trader Trades", example="SML1458")],
                                     input_data: DeleteTradeRequest = Depends()) -> str:
    lambro_logger.info(f"Executing request query to crate a new trade for {trader_id} TradingRecord collection - start")
    delete_trade = TradeDelete(database="Trades", collection="TradingRecord")    
    trades_output = delete_trade.delete_trade(trade_id=input_data.trade_id)
    lambro_logger.info(f"Executing request query to crate a new trade for {trader_id} TradingRecord collection - completed")
    if not trades_output:
        return JSONResponse(status_code=status.HTTP_200_OK, content=[])
    return JSONResponse(status_code=status.HTTP_201_CREATED, content="Created")

