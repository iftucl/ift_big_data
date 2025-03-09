from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Literal
from ift_global.utils.string_utils import trim_string

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

    model_config = ConfigDict(
        title="Trade Response",
        description="A trade schema for trade response",
        json_schema_extra = {
            "example": {
                
            }
        }

    )
