from sqlalchemy import text
from typing import Literal
from modules.db_ops.ift_sql import DatabaseMethods

from modules.utils.local_logger import calibration_logger

sql_query = """
WITH daily_prices AS (
  SELECT 
    symbol_id,
    currency,
    cob_date,
    close_price,
    LAG(close_price) OVER (PARTITION BY symbol_id, currency ORDER BY cob_date) AS prev_close_price,
    LAG(cob_date) OVER (PARTITION BY symbol_id, currency ORDER BY cob_date) AS prev_cob_date
  FROM cash_equity.equity_prices ep
  WHERE cob_date >= '{business_date_pr}' AND cob_date <= '{business_date}'
),
daily_returns AS (
	SELECT 
	  symbol_id,
	  currency,
	  cob_date,
	  close_price,
	  prev_close_price,
	  prev_cob_date,
	  CASE 
	    WHEN prev_close_price IS NOT NULL AND prev_close_price != 0
	    THEN ABS(close_price / prev_close_price - 1)
	    ELSE NULL
	  END AS one_day_return,
	  cob_date - prev_cob_date AS days_between
	FROM daily_prices
)
SELECT 
  gics_sector,
  cob_date,
  AVG(one_day_return) AS abs_avg_return,
  STDDEV(one_day_return) AS abs_stdev_return
FROM daily_returns dr
LEFT JOIN cash_equity.equity_static cs ON dr.symbol_id = cs.symbol
GROUP BY {group_expression}, cob_date;
"""



def get_distribution_params(start_date: str, end_date: str, group_type: Literal["gics_sector", "country", "region"]):
    """
    
    """
    sql_query_fmt = sql_query.format(
        business_date_pr=start_date,
        business_date=end_date,
        group_expression=group_type
    )
    with DatabaseMethods("postgres", username="postgres", password="postgres", host="localhost", port="5438", database="fift") as db:
        try:
            result = db.session.execute(text(sql_query_fmt))
        except Exception as e:
            calibration_logger.error(f"An error occurred: {e}")
            raise
    return result.all()
