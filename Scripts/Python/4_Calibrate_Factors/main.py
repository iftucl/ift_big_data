"""

UCL -- Institute of Finance & Technology
Author  : Luca Cocconcelli
Lecture : 2024-02-21
Topic   : Main.py
Project : SQL Trades aggregator & uploader

"""

from ift_global import ReadConfig
from ift_global.utils.set_env_var import set_env_variables
from sqlalchemy import text
import datetime
import time


from modules.utils.local_logger import calibration_logger
from modules.db_ops.ift_sql import DatabaseMethods
from modules.market_factors.sector_calibration import get_distribution_params
from modules.market_factors.equity_var import calculate_parametric_var


conf = ReadConfig("dev")
set_env_variables(env_variables=conf['config']['env_variables'], env_type="dev", env_file=True)

database_methods = DatabaseMethods(db_type="postgres")

with database_methods.session as s:
    s.execute(text(""))

with DatabaseMethods('postgres',username="postgres", password="postgres", host="localhost", port="5438", database="fift") as db:
    try:
        # Create a session and execute a query
        session = db.session
        result = session.execute(text("""SELECT ct.symbol, ct.float_shares, cs.region, cs.country, cs.gics_sector, ep.currency, (ep.close_price * ex.exchange_rate) AS usd_px FROM cash_equity.company_statistics ct
                                         LEFT JOIN cash_equity.equity_static cs ON ct.symbol = cs.symbol
                                         LEFT JOIN cash_equity.equity_prices ep ON ct.symbol = ep.symbol_id AND ep.cob_date = '2023-11-09'
                                         LEFT JOIN cash_equity.exchange_rates ex ON ep.currency = ex.from_currency AND ex.cob_date = '2023-11-09' AND ex.to_currency = 'USD'
                                         WHERE ep.close_price IS NOT NULL"""))
    except Exception as e:
        print(f"An error occurred: {e}")

result.all()

sector_ret_dist = get_distribution_params(start_date="2023-11-02", end_date="2023-11-09", group_type="gics_sector")

with DatabaseMethods('postgres',username="postgres", password="postgres", host="localhost", port="5438", database="fift") as db:
    try:
        # Create a session and execute a query
        session = db.session
        static_results = session.execute(text("""SELECT * FROM cash_equity.equity_static"""))
    except Exception as e:
        print(f"An error occurred: {e}")
        raise


static_results.all()
