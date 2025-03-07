"""

UCL -- Institute of Finance & Technology
Author  : Luca Cocconcelli
Lecture : 2025-02-21
Topic   : Main.py
Project : Calibrate Market Data Parameters

"""

from ift_global import ReadConfig
from ift_global.utils.set_env_var import set_env_variables
import os


from modules.utils import calibration_logger, arg_parse_cmd, get_previous_business_dates
from modules.input_data.get_input_company_static import get_equity_static
from modules.input_data.get_input_previous_close import get_previous_close_px
from modules.market_factors.sector_calibration import get_distribution_params
from modules.market_factors.equity_var import calculate_parametric_var
from modules.output_data.load_redis_db import load_market_moves_redis



def main():
    calibration_logger.info("Started Calibration of market risk factors")
    args = arg_parse_cmd()
    parsed_args = args.parse_args()
    calibration_logger.info("Command Line argument parsed. Script running for {parsed_args.env_type} on date run {parsed_args.date_run}")
    # example: conf = ReadConfig("dev")
    conf = ReadConfig(parsed_args.env_type)
    # sets environment var, example set_env_variables(env_variables=conf['config']['env_variables'], env_type="dev", env_file=True)
    set_env_variables(env_variables=conf['config']['env_variables'],
                      env_type=parsed_args.env_type,
                      env_file=True)
    calibration_logger.info("Calculating distribution parameters for stocks returns on date run {parsed_args.date_run}")
    date_run=parsed_args.date_run
    # example date_run = "2023-11-23"
    sector_ret_dist = get_distribution_params(start_date=date_run,
                                              end_date=get_previous_business_dates(start_date=date_run, look_back=10),
                                              group_type="gics_sector",
                                              holding_period=5)
    calibration_logger.info("Fetching Company Statics...")
    company_statics = get_equity_static(database="fift")
    calibration_logger.info("Fetching Last Close Price...")
    price_close = get_previous_close_px(cob_date=date_run, database="fift")
    calibration_logger.info("Set output dictionaries for redis load...")
    load_market_moves_redis(company_statics=company_statics, sector_ret_dist=sector_ret_dist, price_close=price_close)
    calibration_logger.info("Script completed")

if __name__ == '__main__':
    main()
