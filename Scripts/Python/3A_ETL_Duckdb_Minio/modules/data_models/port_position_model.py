from sqlmodel import SQLModel, Field
from datetime import datetime

class PortfolioPositions(SQLModel):
    """Table for portfolio positions"""
    __tablename__ = "portfolio_positions"
    __table_args__ = {"schema": "cash_equity"}
    pos_id: str = Field(description="", primary_key=True, schema_extra={"examples": [""]})
    cob_date: datetime = Field(description="", primary_key=True, schema_extra={"examples": [""]})
    trader: str = Field(description="", primary_key=True, schema_extra={"examples": [""]})
    symbol: str = Field(description="", primary_key=True, schema_extra={"examples": [""]})
    ccy: str = Field(description="", primary_key=True, schema_extra={"examples": [""]})
    net_quantity: float = Field(description="", schema_extra={"examples": [""]})
    net_amount: int = Field(description="", schema_extra={"examples": [""]})
