from pydantic import BaseModel, Field, ConfigDict, model_validator, field_validator
from fastapi import Query
from typing import Optional, Literal
from datetime import datetime, timezone

from ift_global.utils.string_utils import trim_string

class TraderTradesRequest(BaseModel):
    offset: Optional[int] = Field(
        Query(default=None, title="Offset trades", description="Offests the n first numbers of trades", example=10, gte=0, lt=100)
    )
    limit: Optional[int] = Field(
        Query(default=None, title="Limit response trade number", description="Limits the number of trades to be included in the response", example=10, gte=0, lt=100)
    )

class AllTradesRequest(TraderTradesRequest):
    search: Optional[int] = Field(
        Query(default=None, title="Search trades by trader id", description="Searches for the trades of a trader based on her/his id.", example="SML")
    )

class DeleteTradeRequest(BaseModel):
    trade_id: str = Field(
        Query(title="Deletes a specific trade", description="Deletes the trade of a trader based on her/his trade id.", example="BDGR1983PHNX.L20231123080108")
    )

class UpdateTradeRequest(BaseModel):
    trade_id: str = Field(
        ..., title="Updates a specific trade", description="Update the trade of a trader based on her/his trade id.", example="BDGR1983PHNX.L20231123080108"
    )
    Quantity: Optional[float] = Field(default=None, description="Quantity value of securities bought or sold")
    Notional: Optional[float] = Field(default=None, description="Monetary value of securities bought or sold")


class CreateTrade(BaseModel):
    DateTime: Optional[datetime] | None = Field(description="Timestamp of the trade", default=None)
    TradeId: Optional[str] | None = Field(description="Unique trade identifier", default=None)
    Trader: str = Field(..., description="Trader identifier")
    Symbol: str = Field(..., description="Traded security identifier")
    Quantity: int = Field(..., description="Quantity of securities bought or sold")
    Notional: float  = Field(..., description="Monetary value of securities bought or sold")
    TradeType: Literal['BUY', 'SELL'] = Field(..., description="If trade is buy or sell")
    Ccy: str = Field(..., description="Currency of trade")
    Counterparty: str = Field(..., description="Counterparty of the trade - who is buying-from or selling-to")
    # validates notional
    @field_validator("DateTime", mode="before")
    @classmethod
    def get_symbol(cls, v) -> int:
        if not v:
            return datetime.now(timezone.utc)
        try:
            return datetime.strptime(v, '%Y-%m-%d %H:%M:%S')
        except ValueError:
            return None
    @model_validator(mode='after')
    def build_trade_id(self):        
        formatted_timestamp = datetime.strftime(self.DateTime, "%Y%m%d%H%M%S")
        self.TradeId = self.TradeType[0] + self.Trader + self.Symbol + formatted_timestamp
        return self
    model_config = ConfigDict(
        title="Trade Response",
        description="A trade schema for trade response",
        json_schema_extra = {
            "example":  {
                "DateTime": "2023-11-23T08:01:08",
                "TradeId": "BDGR1983PHNX.L20231123080108",
                "Trader": "DGR1983",
                "Symbol": "PHNX.L",
                "Quantity": 30000,
                "Notional": 185159.16172365914,
                "TradeType": "BUY",
                "Ccy": "GBP",
                "Counterparty": "MLI"
            }
        }

    )
