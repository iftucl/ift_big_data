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
import os
import datetime
import time


from modules.utils import calibration_logger, arg_parse_cmd, get_previous_business_dates
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



with DatabaseMethods('postgres',username="postgres", password="postgres", host="localhost", port="5438", database="fift") as db:
    try:
        # Create a session and execute a query
        session = db.session
        static_results = session.execute(text("""SELECT * FROM cash_equity.equity_static"""))
    except Exception as e:
        print(f"An error occurred: {e}")
        raise

def main():
    calibration_logger.info("Started Calibration of market risk factors")
    args = arg_parse_cmd()
    parsed_args = args.parse_args()
    calibration_logger.info("Command Line argument parsed. Script running for {parsed_args.env_type} on date run {parsed_args.date_run}")
    # example: conf = ReadConfig("dev")
    conf = ReadConfig(parsed_args.env_type)
    # sets environment var
    set_env_variables(env_variables=conf['config']['env_variables'],
                      env_type=parsed_args.env_type,
                      env_file=True)
    calibration_logger.info("Calculating distribution parameters for stocks returns on date run {parsed_args.date_run}")
    sector_ret_dist = get_distribution_params(start_date=parsed_args.date_run,
                                              end_date=get_previous_business_dates(start_date=parsed_args.date_run, look_back=10),
                                              group_type="gics_sector",
                                              holding_period=5)
    static_results.all()
