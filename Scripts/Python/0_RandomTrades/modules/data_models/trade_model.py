from pydantic import BaseModel, Field, model_validator, field_validator, ValidationInfo
from datetime import datetime
from typing import Literal
from ift_global.utils.string_utils import trim_string
from modules.utils.info_logger import trades_logger

from typing import Optional

class Trade(BaseModel):
    DateTime: datetime = Field(..., description="Timestamp of the trade")
    TradeId: Optional[str] = Field(default=None, description="Unique trade identifier")
    Trader: str = Field(..., description="Trader identifier")
    Symbol: str = Field(..., description="Traded security identifier")
    Quantity: int = Field(..., description="Quantity of securities bought or sold")
    Notional: float  = Field(..., description="Monetary value of securities bought or sold")
    TradeType: Literal['BUY', 'SELL'] = Field(..., description="If trade is buy or sell")
    Ccy: str = Field(..., description="Currency of trade")
    Counterparty: str = Field(..., description="Counterparty of the trade - who is buying-from or selling-to")
    # validates notional
    @field_validator("Symbol", mode="before")
    @classmethod
    def get_symbol(cls, v, info: ValidationInfo) -> int:
        try:
            return trim_string(v, what="trailing")
        except ValueError:
            return None
    @model_validator(mode='after')
    def build_trade_id(self):        
        formatted_timestamp = datetime.strftime(self.DateTime, "%Y%m%d%H%M%S")
        self.TradeId = self.TradeType[0] + self.Trader + self.Symbol + formatted_timestamp
        return self