from modules.db_ops.ift_sql import DatabaseMethods
from modules.utils.local_logger import calibration_logger

sql_query = """SELECT ct.symbol, ct.float_shares, cs.region, cs.country, cs.gics_sector, ep.currency,
(ep.close_price * ex.exchange_rate) AS px_usd,
(ep.close_price * ex.exchange_rate * ct.float_shares) AS mcap_usd FROM cash_equity.company_statistics ct
LEFT JOIN cash_equity.equity_static cs ON ct.symbol = cs.symbol
LEFT JOIN cash_equity.equity_prices ep ON ct.symbol = ep.symbol_id AND ep.cob_date = '{cob_date}'
LEFT JOIN cash_equity.exchange_rates ex ON ep.currency = ex.from_currency AND ex.cob_date = '{cob_date}' AND ex.to_currency = 'USD'
WHERE ct.float_shares IS NOT NULL"""


def get_market_cap(cob_date: str):
    
    with DatabaseMethods("postgres", username="postgres", password="postgres", host="localhost", port="5438", database="fift") as db:
        try:
            result = db.session.execute(text(sql_query_fmt))
        except Exception as e:
            calibration_logger.error(f"An error occurred: {e}")
            raise
    return result.all()
