from datetime import datetime, timedelta
from modules.utils import calibration_logger

def get_previous_business_dates(start_date: str, look_back: int) -> str:
    try:
        date_fmt = datetime.strptime(start_date, "%Y-%m-%d")
    except Exception as Exc:
        calibration_logger.error(f"Error in converting to previous business date {start_date}")
        raise
    end_date = date_fmt - timedelta(days=look_back)
    return end_date.strftime("%Y-%m-%d")
