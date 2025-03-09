from sqlmodel import SQLModel, Field
from typing import Any
from pydantic.functional_validators import field_validator
from datetime import datetime, timezone

class CompanyStatistics(SQLModel, table=True):
    """
    SQLModel representation of the company_statistics table.
    """
    __tablename__ = "company_statistics"
    __table_args__ = {"schema": "fift", "extend_existing": True}

    symbol: str = Field(..., description="The ticker symbol of the company.", nullable=False)
    float_shares: int = Field(description="The number of free-floating shares available for trading.")
    outstanding_shares: int = Field(description="The total number of outstanding shares issued by the company.")
    book_value: float = Field(description="The book value per share of the company.")
    enterprise_revenue: float = Field(description="The enterprise value divided by revenue.")
    enterprise_ebitda: float = Field(description="The enterprise value divided by EBITDA.")
    start_date: str = Field(..., description="The start date for financial data retrieval (stored as ISO 8601 string).", default_factory=lambda: datetime.now(timezone.utc).strftime("%Y-%m-%d"))
    end_date: str = Field(..., description="The end date for financial data retrieval (stored as ISO 8601 string).")
    entry_id: str = Field(..., primary_key=True, description=("Concatenates symbol and date to form primary key"))    
    @field_validator("start_date", mode="before")
    @classmethod
    def set_start_date(cls, v: Any):
        if not v:
            dt_object = datetime.now(timezone.utc)
            return dt_object.strftime("%Y-%m-%d")
        try:
            date_format_check = datetime.strptime(v, "%Y-%m-%d")
            return date_format_check
        except ValueError:
            print("Could not convert to datetime object")
            raise
