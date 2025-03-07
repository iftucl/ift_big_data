"""

UCL -- Institute of Finance & Technology
Author  : Luca Cocconcelli
Lecture : 2025-02-21
Topic   : Main.py
Project : Validate Bulk Trades

"""
from ift_global import ReadConfig
from ift_global.utils.set_env_var import set_env_variables
import os


from modules.utils import trades_validate_logger, arg_parse_cmd
from modules.input.read_file import ReadInputFiles
from modules.analysis.regression_analysis import analyze_trades
from modules.db.mongo_db import LoadMongo

def main():
    trades_validate_logger.info("Started Calibration of market risk factors")
    args = arg_parse_cmd()
    parsed_args = args.parse_args()
    trades_validate_logger.info("Command Line argument parsed. Script running for {parsed_args.env_type} on date run {parsed_args.date_run}")
    # example: conf = ReadConfig("dev")
    conf = ReadConfig(parsed_args.env_type)
    # sets environment var, example set_env_variables(env_variables=conf['config']['env_variables'], env_type="dev", env_file=True)
    set_env_variables(env_variables=conf['config']['env_variables'],
                      env_type=parsed_args.env_type,
                      env_file=True)
    trades_validate_logger.info("Calculating distribution parameters for stocks returns on date run {parsed_args.date_run}")
    # example: "/iftbigdata/DataLake/Trades/EquityTrades_20250202110516.csv"
    file_reader=ReadInputFiles(file_config=conf["params"]["OutputFile"])
    trades_check = file_reader.read_dictionary()
    trades_validate_logger.info("File found in directory... Moving into checks.")
    # Example usage
    unique_ids = set(x.Symbol for x in trades_check)
    for un_id in unique_ids:
        trades = [x for x in trades_check if x.Symbol == un_id]
        if len(trades) > 10:
            # if we have enough trades we test confidence interval
            analysis_results = analyze_trades(trades)
        else:
            # we fall back on the pre-calibrated params
            analysis_results = test_trades(trades)
    mongo_loader = LoadMongo(mongo_config=conf['config']['Database']['Mongo'])    
    mongo_loader.load_mongo_data(analysis_results)
