from pydantic import BaseModel, Field, field_validator, ValidationInfo
from datetime import datetime, timezone
from ift_global.utils.string_utils import trim_string

from modules.utils.local_logger import lambro_logger
from app.api_models.api_responses.trade_model import Trade

class TradeSuspect(Trade):
    ValidationTime: datetime | None = Field(description="Timestamp of the validation")
    ValidationLabel: str = Field(..., description="Validation Type")
    IsSuspect: bool = Field(..., description="True if this trade is a suspect")
    @field_validator("ValidationTime", mode="before")
    def get_time_stamp(cls, v, info: ValidationInfo) -> datetime:
        if v:
            try:
                if isinstance(v, datetime):
                    return v
                return datetime.strptime(v, '%Y-%m-%d %H:%M:%S%z')
            except ValueError:            
                lambro_logger.error(f"Could not convert to datetime for time stamp: {v}")
        return datetime.now(timezone.utc)
