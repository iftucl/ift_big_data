from sqlmodel import SQLModel, Field

class EquityPrices(SQLModel, table=True):
    """
    SQLModel representation of the equity_prices table.
    """
    __tablename__ = "equity_prices"
    __table_args__ = {"schema": "fift", "extend_existing": True}

    price_id: str = Field(primary_key=True, description="Unique identifier for the price record.")
    open_price: int = Field(default=None, description="The opening price of the equity.")
    close_price: int = Field(..., description="The closing price of the equity.")
    volume: int = Field(..., description="The volume of shares traded.")
    currency: str = Field(..., description="The currency in which prices are quoted.")
    cob_date: str = Field(..., description="The close of business date (YYYY-MM-DD).")
    symbol_id: str = Field(..., foreign_key="equity_static.symbol", description="Foreign key referencing equity_static table.")

