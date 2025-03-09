from sqlmodel import SQLModel, Field

class EquityStatic(SQLModel, table=True):
    """
    SQLModel representation of the equity_static table.
    """
    __tablename__ = "equity_static"
    __table_args__ = {"schema": "fift", "extend_existing": True}

    symbol: str = Field(primary_key=True, description="The unique symbol for the equity.")
    security: str = Field(default=None, description="The name of the security.")
    gics_sector: str = Field(default=None, description="The GICS sector of the equity.")
    gics_industry: str = Field(default=None, description="The GICS industry of the equity.")
    country: str = Field(max_length=2, description="The country code like 'US'.")
    region: str = Field(description="The region of the equity like 'North America'.")
