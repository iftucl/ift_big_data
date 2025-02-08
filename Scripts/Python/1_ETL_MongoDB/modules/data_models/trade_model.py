from pydantic import BaseModel, Field, field_validator, ValidationInfo
from datetime import datetime
from typing import Literal
from ift_global.utils.string_utils import trim_string
from modules.utils.info_logger import etl_mongo_logger

class Trade(BaseModel):
    DateTime: datetime = Field(..., description="Timestamp of the trade")
    TradeId: str = Field(..., description="Unique trade identifier")
    Trader: str = Field(..., description="Trader identifier")
    Symbol: str = Field(..., description="Traded security identifier")
    Quantity: int = Field(..., description="Quantity of securities bought or sold")
    Notional: float  = Field(..., description="Monetary value of securities bought or sold")
    TradeType: Literal['BUY', 'SELL'] = Field(..., description="If trade is buy or sell")
    Ccy: str = Field(..., description="Currency of trade")
    Counterparty: str = Field(..., description="Counterparty of the trade - who is buying-from or selling-to")
    @field_validator("Notional", mode="before")
    def get_notional(cls, v):
        try:
            return float(v)
        except ValueError:
            return None
    @field_validator("Quantity", mode="before")
    def get_quantity(cls, v, info: ValidationInfo) -> float:
        try:
            return int(v)
        except ValueError:
            return None
    @field_validator("Symbol", mode="before")
    def get_symbol(cls, v, info: ValidationInfo) -> int:
        try:
            return trim_string(v, what="trailing")
        except ValueError:
            return None
    @field_validator("DateTime", mode="before")
    def get_time_stamp(cls, v, info: ValidationInfo) -> datetime:
        try:
            return datetime.strptime(v, '%Y-%m-%d %H:%M:%S%z')
        except ValueError:            
            etl_mongo_logger.error(f"Could not convert to datetime for time stamp: {v}")
