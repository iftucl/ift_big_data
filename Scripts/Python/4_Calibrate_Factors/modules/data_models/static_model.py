from pydantic import BaseModel, Field, field_validator, ValidationInfo
from ift_global.utils.string_utils import trim_string


class EquityStatic(BaseModel):
    company_id: str = Field(..., description="Traded security identifier")
    company_name: str = Field(..., description="Company Name")
    sector_name: str  = Field(..., description="Sector name for this company")
    industry_name: str = Field(..., description="industry name for this company")
    country_id: str = Field(..., description="Country id as 'US'", min_length=2, max_length=2)
    region_name: str = Field(..., description="Region for this company")    
    # validates notional
    @field_validator("company_id", mode="before")
    @classmethod
    def get_symbol(cls, v) -> int:
        try:
            return trim_string(v, what="trailing")
        except ValueError:
            return None
