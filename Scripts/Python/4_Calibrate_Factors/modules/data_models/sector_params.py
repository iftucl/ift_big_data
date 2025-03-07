from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class SectorParams(BaseModel):
    sector_name: str
    params_date: datetime
    sector_average: Optional[float]
    sector_stdev: Optional[float]

