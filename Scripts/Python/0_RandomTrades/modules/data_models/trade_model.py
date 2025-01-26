from pydantic import BaseModel, Field
from datetime import datetime
from typing import Literal

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
