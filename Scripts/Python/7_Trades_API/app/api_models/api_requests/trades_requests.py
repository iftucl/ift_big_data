from pydantic import BaseModel, Field
from fastapi import Query
from typing import Optional

class AllTradesRequest(BaseModel):
    offset: Optional[int] = Field(
        Query(default=None, title="Offset trades", description="Offests the n first numbers of trades", example=10, gte=0, lt=100)
    )
    limit: Optional[int] = Field(
        Query(default=None, title="Limit response trade number", description="Limits the number of trades to be included in the response", example=10, gte=0, lt=100)
    )
    search: Optional[int] = Field(
        Query(default=None, title="Search trades by trader id", description="Searches for the trades of a trader based on her/his id.", example=10, gte=0, lt=100)
    )