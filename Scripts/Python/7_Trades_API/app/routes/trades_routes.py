from fastapi import APIRouter, Depends, status, Path
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from typing import Annotated

from modules.utils.local_logger import lambro_logger
from app.api_models.api_requests.trades_requests import AllTradesRequest, TraderTradesRequest, CreateTrade, DeleteTradeRequest, UpdateTradeRequest
from app.api_models.api_responses.trade_model import Trade
from app.modules.mongodb_trades_get import TradeQuery, TradeInsert, TradeDelete, TradeUpdate
from app.modules.redis_suspects_analysis import test_trades_peers

router = APIRouter()

@router.get("/trades", summary="Gets all trades", description="Returns a full list of trades")
async def get_all_trades_endpoint(input_data: AllTradesRequest = Depends()) -> list[Trade]:
    lambro_logger.info(f"Executing request query to get all trades in TradingRecord collection - start")
    mongo_trades = TradeQuery(database="Trades", collection="TradingRecord")
    trades_output = mongo_trades.get_trades(limit=input_data.limit, query_field=None)
    lambro_logger.info(f"Executing request query to get all trades in TradingRecord collection - completed")
    if not trades_output:
        return JSONResponse(status_code=status.HTTP_200_OK, content=[])
    return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(trades_output))

@router.get("/trades/{trader_id}", summary="Gets all trades", description="Returns a full list of trades")
async def get_trader_trades_endpoint(trader_id: Annotated[str, Path(description="Get all trades by trader", title="Trader Trades", example="SML1458")],
                                     input_data: TraderTradesRequest = Depends()) -> list[Trade]:
    lambro_logger.info(f"Executing request query to get {trader_id} trades in TradingRecord collection - start")
    mongo_trades = TradeQuery(database="Trades", collection="TradingRecord")
    trades_output = mongo_trades.get_trades(limit=input_data.limit, match=trader_id, query_field="Trader")
    lambro_logger.info(f"Executing request query to get {trader_id} trades in TradingRecord collection - completed")
    if not trades_output:
        return JSONResponse(status_code=status.HTTP_200_OK, content=[])    
    return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(trades_output))

@router.get("/trades/{trader_id}/suspects", summary="Gets all suspect trades", description="Returns a full list of trade suspects")
async def get_all_suspects_endpoint(trader_id: Annotated[str, Path(description="Get all trades by trader", title="Trader Trades", example="SML1458")]) -> list[Trade]:
    lambro_logger.info(f"Executing request query to get all trade suspects in TradingRecord collection - start")
    mongo_trades = TradeQuery(database="Trades", collection="SuspectTrades")
    trades_output = mongo_trades.get_trades(match=trader_id, query_field="Trader")
    lambro_logger.info(f"Executing request query to get all trades in TradingRecord collection - completed")
    if not trades_output:
        return JSONResponse(status_code=status.HTTP_200_OK, content=[])
    return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(trades_output))

@router.get("/trades/{trader_id}/{trade_id}", summary="Gets a trade for a trader", description="Returns a a specific trade given the trader id and trade id")
async def get_trader_trade_endpoint(trader_id: Annotated[str, Path(description="Get all trades by trader", title="Trader Trades", example="SML1458")],
                                     trade_id: Annotated[str, Path(description="Get all trades by trader", title="Trader Trades", example="SSML1458BT-A.L20231123082457")],
                                     input_data: TraderTradesRequest = Depends()) -> list[Trade]:
    lambro_logger.info(f"Executing request query to get for {trader_id} the trade {trade_id} in TradingRecord collection - start")
    mongo_trades = TradeQuery(database="Trades", collection="TradingRecord")
    trades_output = mongo_trades.get_trade_from_id(trade_id=trade_id)
    lambro_logger.info(f"Executing request query to get for {trader_id} the trade {trade_id} in TradingRecord collection - completed")
    if not trades_output:
        return JSONResponse(status_code=status.HTTP_200_OK, content=[])    
    return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(trades_output))

@router.get("/trades/{trader_id}/{trade_id}/suspect", summary="Gets the validation for a trade", description="Returns a a specific validation rule for a trade given the trader id and trade id")
async def get_trade_suspect_endpoint(trader_id: Annotated[str, Path(description="Get all trades by trader", title="Trader Trades", example="SML1458")],
                                     trade_id: Annotated[str, Path(description="Get all trades by trader", title="Trader Trades", example="BSML1458TW.L20231123142447")]) -> list[Trade]:
    lambro_logger.info(f"Executing request query to get for {trader_id} the trade {trade_id} in TradingRecord collection - start")
    mongo_trades = TradeQuery(database="Trades", collection="SuspectTrades")
    trades_output = mongo_trades.get_trade_from_id(trade_id=trade_id)
    lambro_logger.info(f"Executing request query to get for {trader_id} the trade {trade_id} in TradingRecord collection - completed")
    if not trades_output:
        return JSONResponse(status_code=status.HTTP_200_OK, content=[])    
    return JSONResponse(status_code=status.HTTP_200_OK, content=jsonable_encoder(trades_output))



@router.post("/trades/{trader_id}/submit-trade", summary="Create a new trade", description="For a trader, creates a new trade")
async def post_trader_trade_endpoint(trader_id: Annotated[str, Path(description="Endpoint for trader to submit its trades", title="Trader Trade Send", example="SML1458")],
                                     input_data: CreateTrade = Depends()) -> list[Trade]:    
    lambro_logger.info(f"Executing request query to create a new trade for {trader_id} TradingRecord collection - start")
    lambro_logger.info(f"Executing tarde validation on request query to create a new trade for {trader_id} - start")
    tested_trade_async = test_trades_peers(single_trade=input_data, confidence_level=0.01)
    lambro_logger.info(f"Executing tarde validation on request query to create a new trade for {trader_id} - completed")
    insert_trades = TradeInsert(database="Trades", collection="TradingRecord")    
    trades_output = insert_trades.insert_trade(input_data)
    lambro_logger.info(f"Executing request query to create a new trade for {trader_id} TradingRecord collection - completed")
    try:
        tested_trade_awaited = await tested_trade_async
        insert_trades = TradeInsert(database="Trades", collection="SuspectTrades")    
        trades_output = insert_trades.insert_trade(tested_trade_awaited)
        lambro_logger.info(f"Executing request query to create a new trade for {trader_id} TradingRecord collection - completed")
    except Exception as exc:
        lambro_logger.error(f"an error occurred while loading suspect data to mongodb for {trader_id} with exception: {exc}")
        return JSONResponse(status_code=status.HTTP_201_CREATED, content={"Result": "Created", "ValidationStatus": "SystemFailure"})
    if not trades_output:
        return JSONResponse(status_code=status.HTTP_200_OK, content=[])
    return JSONResponse(status_code=status.HTTP_201_CREATED, content={"Result": "Created",
                                                                       "ValidationStatus": tested_trade_awaited.IsSuspect,
                                                                       "TradeId": input_data.TradeId})

@router.delete("/trades/{trader_id}/delete-trade", summary="Delete trade", description="For a trader, deletes a trade")
async def post_trader_trade_endpoint(trader_id: Annotated[str, Path(description="Get all trades by trader", title="Trader Trades", example="SML1458")],
                                     input_data: DeleteTradeRequest = Depends()) -> str:
    lambro_logger.info(f"Executing request query to delete a new trade for {trader_id} TradingRecord collection - start")
    delete_trade = TradeDelete(database="TradingRecord", collection="TradingRecord")    
    trades_output = delete_trade.delete_trade(trade_id=input_data.trade_id)
    lambro_logger.info(f"Executing request query to delete trade for {trader_id} TradingRecord collection - completed")
    if not trades_output:
        return JSONResponse(status_code=status.HTTP_200_OK, content=[])
    return JSONResponse(status_code=status.HTTP_201_CREATED, content="Created")

@router.put("/trades/{trader_id}/amend-trade", summary="Update trade", description="For a trader, updates the trade fields")
async def put_trader_trade_endpoint(trader_id: Annotated[str, Path(description="Get all trades by trader", title="Trader Trades", example="SML1458")],
                                    input_data: UpdateTradeRequest = Depends()) -> str:
    lambro_logger.info(f"Executing request query to update a trade for {trader_id} TradingRecord collection - start")
    update_trade = TradeUpdate(database="TradingRecord", collection="TradingRecord")    
    trades_output = update_trade.update_trade(trade_id=input_data.trade_id, notional=input_data.Notional, quantity=input_data.Quantity)
    lambro_logger.info(f"Executing request query to update a trade for {trader_id} TradingRecord collection - completed")
    if not trades_output:
        return JSONResponse(status_code=status.HTTP_200_OK, content=[])
    return JSONResponse(status_code=status.HTTP_200_OK, content="Created")




